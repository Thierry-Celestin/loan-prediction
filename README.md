# Loan Approval Prediction Web Application and Monitoring System

This repository contains the source code, Airflow DAGs, and documentation for a Loan Approval Prediction System. The system features a web application for loan approval predictions, automated data ingestion, and monitoring tools to ensure data and model integrity.

## Project Structure

### 1. **Web Application, API, and Database**

#### **Web Application**
- Built with Streamlit, providing a user-friendly interface for loan approval predictions.
- **Prediction Page**: Users can input loan data manually or upload CSVs for batch predictions and receive real-time results.
- **Past Predictions Page**: Displays historical predictions, filtered by date or input type (manual vs. batch).

#### **API (Model Service)**
- Developed with FastAPI to serve predictions.
- **Endpoints**:
  - `/predict`: Accepts loan application data for single or batch predictions.
  - `/past-predictions`: Retrieves historical prediction data.

#### **Database**
- PostgreSQL stores historical predictions, making them accessible through the web app and API for future reference.

---

### 2. **Data Issue Generation Notebook**
- Jupyter Notebook designed to simulate and introduce data quality issues in the loan application dataset.
- Issues introduced:
  - **Missing Values**: Introduces missing data for required fields.
  - **Outliers**: Inserts extreme values in numeric fields.
  - **Data Type Mismatches**: Simulates incorrect data types.

---

### 3. **Data Generation Script**
- `loan_approval_splitting_files.py` generates loan application data in CSV format.
- Mimics real-time submissions, creating raw data files to be processed by the ingestion pipeline.

---

### 4. **Data Ingestion Pipeline**
- Managed through an Apache Airflow DAG for automated data ingestion and validation.
  
#### **Airflow DAG: Data Ingestion**
- **Tasks**:
  1. `read-data`: Reads raw loan application data from the `raw-data` folder.
  2. `validate-and-move`: Validates data integrity (e.g., missing values, data types) and moves valid data to the `good-data` folder.

---

### 5. **Prediction Job Pipeline**
- Another Airflow DAG automates predictions based on newly ingested data.

#### **Airflow DAG: Prediction Job**
- **Tasks**:
  1. `check_for_new_data`: Scans the `good-data` folder for new files.
  2. `make_predictions`: Sends the new data to the prediction model API, stores results in the database.

---

## Installation

### **Prerequisites**
- Python 3.7+
- PostgreSQL
- Docker (optional, recommended for deployment)
- Airflow

### **Setup Instructions**
1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/loan_approval_prediction.git
    cd loan_approval_prediction
    ```
2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Start the FastAPI model service:
    ```bash
    uvicorn app.main:app --reload
    ```
5. Start the Streamlit web application:
    ```bash
    streamlit run app/webapp.py
    ```

---

## Usage

### **Web Application**
- Access the prediction page: `http://127.0.0.1:8501`
- Submit loan data manually or upload CSV files for batch predictions.

### **API (Model Service)**
- Make predictions via a POST request to `/predict`:
    ```bash
    curl -X POST 'http://127.0.0.1:8000/predict' \
    -H 'Content-Type: application/json' \
    -d '{"loan_amount": 10000, "income": 50000, ...}'
    ```
- Retrieve past predictions via GET request to `/past-predictions`.

### **Airflow DAGs**
- Access the Airflow UI to trigger and monitor the `data_ingestion_dag` and `prediction_job_dag`. Both DAGs can run on a schedule or be manually triggered.

---

## Contributors
- Sravan Kumar Mudireddy
- Niveda Nadarassin
- Madhukesava Natava
- Thierry Celestin Legue Doho
- Ananya Gownivari Ravindrareddy

---

## Support
For support or inquiries, please contact us.