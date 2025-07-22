from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import os
import random
import shutil
import logging

# Folder paths within the container
RAW_DATA_FOLDER = '/opt/airflow/data/raw_data'
GOOD_DATA_FOLDER = '/opt/airflow/data/good_data'
BAD_DATA_FOLDER = '/opt/airflow/data/bad_data'

# Load Microsoft Teams webhook URL from environment variables
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "https://epitafr.webhook.office.com/webhookb2/f1019b08-a732-4629-9d6c-71ae099a1ab8@3534b3d7-316c-4bc9-9ede-605c860f49d2/IncomingWebhook/98613744245c4ecaa14804025dde45ae/a60e4745-65fd-42a0-b620-8f8baa403ad1/V22TCvHdPTjPnm4qYKq79k2bKo17S1xH8FtgFPS-b1Ib41")

# Ensure that 'good_data' and 'bad_data' folders exist
def ensure_folders_exist():
    for folder in [GOOD_DATA_FOLDER, BAD_DATA_FOLDER]:
        os.makedirs(folder, exist_ok=True)

# Task 1: Read one random file from 'raw_data' folder
def read_data(**kwargs):
    ensure_folders_exist()
    files = os.listdir(RAW_DATA_FOLDER)
    if not files:
        raise FileNotFoundError("No files in the 'raw_data' folder.")
    
    selected_file = random.choice(files)
    file_path = os.path.join(RAW_DATA_FOLDER, selected_file)
    kwargs['ti'].xcom_push(key='file_path', value=file_path)
    return file_path

# Task 2: Validate data using Great Expectations
def validate_data(**kwargs):
    import pandas as pd
    import great_expectations as ge

    file_path = kwargs['ti'].xcom_pull(key='file_path')
    df = pd.read_csv(file_path)
    ge_df = ge.from_pandas(df)

    # Define validation expectations based on the attached CSV file's structure
    expectations = [
        # Essential columns check with flexibility for extra columns
        ge_df.expect_table_columns_to_match_set(
            [
                'dependents', 'education', 'employment', 'annual_income',
                'loan_amount', 'loan_term', 'cibil_score', 'loan_status'
            ], exact_match=False
        ),

        # Check for missing values in critical columns ('education')
        ge_df.expect_column_values_to_not_be_null('education'),

        # Ensure 'employment' does not contain 'Unknown'
        ge_df.expect_column_values_to_be_in_set(
            'employment', value_set=['employed', 'unemployed', 'self-employed', 'other']
        ),

        # Ensure 'loan_amount' is non-negative
        ge_df.expect_column_values_to_be_between(
            'loan_amount', min_value=0, allow_cross_type_comparisons=True
        ),

        # Check 'cibil_score' is numeric (allow only integers)
        ge_df.expect_column_values_to_match_regex('cibil_score', regex=r'^\d+$'),

        # Ensure 'loan_status' is not missing
        ge_df.expect_column_values_to_not_be_null('loan_status'),

        # Validate 'loan_term' within a reasonable range (1-360 months)
        ge_df.expect_column_values_to_be_between('loan_term', min_value=1, max_value=360)
    ]

    # Assess validation success with a threshold for passing
    failed_expectations = [result for result in expectations if not result['success']]
    num_failures = len(failed_expectations)
    
    # Set a threshold for failures: allow minor issues but fail if critical ones fail
    minor_issues_threshold = 1  # Number of issues allowed before marking as "bad"
    validation_success = num_failures <= minor_issues_threshold

    # Push validation result to XCom
    kwargs['ti'].xcom_push(key='validation_success', value=validation_success)

    # Trigger an alert if validation fails
    if not validation_success:
        failed_columns = [
            exp['expectation_config']['kwargs'].get('column', 'N/A')
            for exp in failed_expectations
        ]
        send_teams_alert(file_path, failed_columns)

    return validation_success

# Function to send an alert to Microsoft Teams if validation fails
def send_teams_alert(file_path, failed_columns):
    import requests

    message = {
        "title": "Data Validation Failed",
        "text": f"Validation failed for file: {os.path.basename(file_path)}. Failed columns: {', '.join(failed_columns)}"
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=message, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send alert to Teams: {e}")

# Task 3: Move file to either 'good_data' or 'bad_data' folder based on validation
def move_file(**kwargs):
    file_path = kwargs['ti'].xcom_pull(key='file_path')
    validation_success = kwargs['ti'].xcom_pull(key='validation_success')
    
    if validation_success:
        shutil.move(file_path, os.path.join(GOOD_DATA_FOLDER, os.path.basename(file_path)))
    else:
        shutil.move(file_path, os.path.join(BAD_DATA_FOLDER, os.path.basename(file_path)))

# Task 4: Send alert if validation fails
def send_alerts(**kwargs):
    validation_success = kwargs['ti'].xcom_pull(key='validation_success')
    if not validation_success:
        file_path = kwargs['ti'].xcom_pull(key='file_path')
        failed_columns = kwargs['ti'].xcom_pull(key='failed_columns', default=[])
        send_teams_alert(file_path, failed_columns)

# Task 5: Save validation statistics
def save_statistics(**kwargs):
    validation_success = kwargs['ti'].xcom_pull(key='validation_success')
    file_path = kwargs['ti'].xcom_pull(key='file_path')
    
    statistics = {
        "file": os.path.basename(file_path),
        "validation_success": validation_success
    }
    # Log statistics (could also save to a database or other storage)
    logging.info(f"Statistics saved: {statistics}")

# DAG definition
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}

with DAG(
    dag_id='data_ingestion_with_teams_alert_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:
    
    # Task definitions
    read_data_task = PythonOperator(
        task_id='read_data',
        python_callable=read_data
    )
    
    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data
    )
    
    send_alerts_task = PythonOperator(
        task_id='send_alerts',
        python_callable=send_alerts
    )
    
    move_file_task = PythonOperator(
        task_id='move_file',
        python_callable=move_file
    )

    save_statistics_task = PythonOperator(
        task_id='save_statistics',
        python_callable=save_statistics
    )

    # Task dependencies to match the screenshot structure
    read_data_task >> validate_data_task
    validate_data_task >> [send_alerts_task, move_file_task, save_statistics_task]
