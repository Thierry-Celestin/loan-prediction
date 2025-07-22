import streamlit as st
import requests
import pandas as pd

st.title("Loan Prediction App")

user_input = st.selectbox("User Input", ("Single Prediction", "Multiple prediction"))

if user_input == "Multiple prediction":
    uploadedFile = st.file_uploader("Upload CSV", type=['csv', 'xlsx'], accept_multiple_files=False)

    if uploadedFile is not None:
        df = pd.read_csv(uploadedFile)
        input_data = {'input': df.to_dict(orient='records')}

        # Only process and display the output after the user clicks the submit button
        file_button = st.button("submit")

        if file_button:
            prediction_url = "http://localhost:8000/prediction"
            response = requests.post(prediction_url, json=input_data)

            if response.status_code == 200:
                predictions = response.json()
                prediction_df = pd.DataFrame(predictions['output'], columns=['Loan_status'])
                result_df = pd.concat([df, prediction_df], axis=1)
                st.dataframe(result_df, hide_index=True)
            else:
                st.write("Error loading API")

else:
    with st.form("user_input"):
        dependents = st.number_input("No of Dependents", min_value=0, value=1)  # Default to 1 dependent
        education = st.selectbox("Graduation status", ("Graduate", "Not Graduate"), index=0)  # Default to "Graduate"
        employment = st.selectbox("Self-employed", ("Yes", "No"), index=1)  # Default to "No" (Not self-employed)
        annual_income = st.number_input("Enter Annual Income", min_value=0, value=50000)  # Default to 50,000
        loan_amount = st.number_input("Enter Loan Amount", min_value=0, value=200000)  # Default to 200,000
        loan_term = st.number_input("Enter Loan Term (in months)", min_value=3, max_value=100, value=12)  # Default to 12 months
        cibil_score = st.number_input("Enter CIBIL score", max_value=999, value=750)  # Default to 750 CIBIL score

        button = st.form_submit_button('Submit')

    predict_url = "http://localhost:8000/prediction"
    if button:
        input_data = {
            "dependents": dependents,
            "education": education,
            "employment": employment,
            "annual_income": annual_income,
            "loan_amount": loan_amount,
            "loan_term": loan_term,
            "cibil_score": cibil_score
        }
        response = requests.post(predict_url, json=input_data)
        if response.status_code == 200:
            result = response.json()
            st.write(f"Your Loan is: **{result['output']}**")
        else:
            st.write("Error loading API")
