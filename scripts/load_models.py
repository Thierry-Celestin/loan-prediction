import os
import psycopg2
import joblib
import pickle  # Import pickle for in-memory serialization

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="loan_pred",
    user="postgres",
    password="data"
)
cursor = conn.cursor()

def store_model_in_db(model, model_name):
    """Serialize and store a model in PostgreSQL."""
    # Serialize model using pickle
    model_data = pickle.dumps(model)
    cursor.execute(
        """
        INSERT INTO models (name, model_data) 
        VALUES (%s, %s) 
        ON CONFLICT (name) DO UPDATE SET model_data = EXCLUDED.model_data;
        """,
        (model_name, psycopg2.Binary(model_data))
    )
    conn.commit()

# Load your models using the correct path
base_dir = os.path.dirname(__file__)  # Get the directory of the current script
le = joblib.load(os.path.join(base_dir, '../models/label_encoder.joblib'))
scaler = joblib.load(os.path.join(base_dir, '../models/scaler.joblib'))
model = joblib.load(os.path.join(base_dir, '../models/logistic_regression_model.joblib'))

# Store the models in the database
store_model_in_db(le, 'label_encoder')
store_model_in_db(scaler, 'scaler')
store_model_in_db(model, 'logistic_model')

cursor.close()
conn.close()

print("Models have been successfully stored in the database.")

