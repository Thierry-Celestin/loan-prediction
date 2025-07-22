from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import pandas as pd
import os
import requests

# DAG configuration
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

# Define the path to the good_data folder where ingested data files are stored
GOOD_DATA_FOLDER = "/opt/airflow/data/good_data"

# Define the FastAPI prediction service URL
PREDICTION_API_URL = "http://fastapi:8000/prediction"

def check_for_new_data(**context):
    processed_files = set(context.get("ti").xcom_pull(key="processed_files", default=[]))
    new_files = []

    # Check for new CSV files in the good_data folder
    for file_name in os.listdir(GOOD_DATA_FOLDER):
        if file_name.endswith(".csv") and file_name not in processed_files:
            new_files.append(file_name)

    # Push new files to XCom and decide which task to follow
    if new_files:
        context["ti"].xcom_push(key="new_files", value=new_files)
        return "make_predictions"
    else:
        return "end"

def make_predictions(**context):
    # Pull the new files from XCom
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_data")
    predictions = []

    # Loop through each new file to make predictions
    for file_name in new_files:
        file_path = os.path.join(GOOD_DATA_FOLDER, file_name)
        data = pd.read_csv(file_path)
        payload = {"input": data.to_dict(orient="records")}
        
        try:
            response = requests.post(PREDICTION_API_URL, json=payload)
            response.raise_for_status()  # Raise error if response is unsuccessful
            predictions.extend(response.json().get("output", []))  # Assuming response contains predictions
            print(f"Predictions for {file_name}: {predictions}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to get predictions for {file_name}: {e}")
            predictions.append(None)

    # Update processed files list in XCom
    processed_files = context.get("ti").xcom_pull(key="processed_files", default=[])
    processed_files.extend(new_files)
    context["ti"].xcom_push(key="processed_files", value=processed_files)
    return predictions

# Define the DAG
with DAG(
    "prediction_dag",
    default_args=default_args,
    description="A DAG for automatic loan prediction",
    schedule_interval="*/2 * * * *",
    start_date=days_ago(1),
    catchup=False,
) as dag:

    check_for_new_data_task = BranchPythonOperator(
        task_id="check_for_new_data",
        python_callable=check_for_new_data,
    )

    make_predictions_task = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions,
    )

    end_task = DummyOperator(task_id="end")

    # Task dependencies
    check_for_new_data_task >> make_predictions_task

