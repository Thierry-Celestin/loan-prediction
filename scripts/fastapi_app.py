from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
import pandas as pd
import psycopg2
import pickle
import numpy as np
import os
from datetime import datetime
import time  # For retrying database connections

app = FastAPI()

# Determine if running inside Docker
RUNNING_IN_DOCKER = os.getenv("DOCKER_ENV", "false").lower() == "true"

# PostgreSQL database connection details
DATABASE_CONFIG = {
    "host": "postgres" if RUNNING_IN_DOCKER else "localhost",
    "database": os.getenv("POSTGRES_DB", "loan_pred"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "data")
}

# Function to connect to PostgreSQL with retries
def get_db_connection(retries=5, delay=2):
    attempt = 0
    while attempt < retries:
        try:
            return psycopg2.connect(**DATABASE_CONFIG)
        except psycopg2.OperationalError as e:
            attempt += 1
            print(f"Database connection attempt {attempt} failed: {e}")
            if attempt >= retries:
                raise HTTPException(status_code=500, detail="Database connection failed")
            time.sleep(delay)

# Establish initial connection to load models
try:
    conn = get_db_connection()
    cursor = conn.cursor()
except HTTPException:
    print("Failed to connect to the database.")
    conn = None
    cursor = None

def load_model_from_db(model_name):
    cursor.execute("SELECT model_data FROM models WHERE name = %s", (model_name,))
    result = cursor.fetchone()
    if result:
        return pickle.loads(result[0])
    else:
        raise ValueError(f"Model {model_name} not found in the database.")

# Load models from the database at startup
try:
    le = load_model_from_db('label_encoder')
    scaler = load_model_from_db('scaler')
    model = load_model_from_db('logistic_model')
    print("Models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")
    raise

class LoanPrediction(BaseModel):
    dependents: int
    education: str
    employment: str
    annual_income: int
    loan_amount: int
    loan_term: int
    cibil_score: int

class MultiPrediction(BaseModel):
    input: List[LoanPrediction]

def preprocess_and_predict(new_data):
    new_data['employment'] = new_data['employment'].str.strip().str.capitalize()
    new_data['employment'] = new_data['employment'].replace({'No': 0, 'Yes': 1})
    new_data['education'] = new_data['education'].str.strip()
    new_data['education'] = new_data['education'].replace({'Graduate': 0, 'Not Graduate': 1})
    x_new = new_data[['dependents', 'education', 'employment', 'annual_income', 'loan_amount', 'loan_term', 'cibil_score']]
    x_new_scaled = scaler.transform(x_new)
    predictions = model.predict(x_new_scaled)
    return ["Approved" if int(pred) == 0 else "Rejected" for pred in predictions]

def save_prediction_to_db(data: pd.DataFrame, predictions: List[str]):
    conn = get_db_connection()  # Re-establish connection
    cursor = conn.cursor()
    for i, prediction in enumerate(predictions):
        cursor.execute(
            """
            INSERT INTO predictions (dependents, education, employment, annual_income, 
                                     loan_amount, loan_term, cibil_score, prediction, prediction_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                int(data.loc[i, 'dependents']),
                str(data.loc[i, 'education']),
                str(data.loc[i, 'employment']),
                int(data.loc[i, 'annual_income']),
                int(data.loc[i, 'loan_amount']),
                int(data.loc[i, 'loan_term']),
                int(data.loc[i, 'cibil_score']),
                prediction,
                datetime.now()
            )
        )
    conn.commit()
    cursor.close()
    conn.close()

@app.post("/prediction")
async def predict(data: Union[LoanPrediction, MultiPrediction]):
    try:
        if isinstance(data, MultiPrediction):
            data_dicts = [item.dict() for item in data.input]
            df = pd.DataFrame(data_dicts).astype({
                "dependents": int, 
                "annual_income": int, 
                "loan_amount": int, 
                "loan_term": int, 
                "cibil_score": int
            })
            output = preprocess_and_predict(df)
            save_prediction_to_db(df, output)
            return {'output': output}
        
        else:
            df = pd.DataFrame([data.dict()]).astype({
                "dependents": int, 
                "annual_income": int, 
                "loan_amount": int, 
                "loan_term": int, 
                "cibil_score": int
            })
            prediction = preprocess_and_predict(df)[0]
            save_prediction_to_db(df, [prediction])
            return {'output': prediction}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
