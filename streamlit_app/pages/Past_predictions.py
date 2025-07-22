import streamlit as st
import requests
import pandas as pd


st.header('Past Predictions')
start_date = st.date_input("Start Date", value=None)
end_date = st.date_input("End Date", value=None)
selected = st.selectbox("Choose Source", ("webapp", "Scheduled", "All"))
button = st.button('Retrieve')

if button:
    url = "http://127.0.0.1:8000/retrieve"
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "source": selected
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        predictions = response.json()
        df = pd.DataFrame(predictions)
        column_order = ['id', 'created_date', 'created_time', 'source', 'dependants', 'education', 'employment',
                        'annual_income', 'loan_amount', 'loan_term', 'cibil_score', 'result']
        df = df.reindex(columns=column_order)
        st.dataframe(df,hide_index=True)

    else:
        st.error("Failed to retrieve predictions")
        