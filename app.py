import streamlit as st
import pandas as pd
import requests
import time
import os

API_KEY = st.secrets["NUMVERIFY_API_KEY"]
BASE_URL = 'http://apilayer.net/api/validate'

def normalize_phone_number(phone):
    digits = ''.join(filter(str.isdigit, str(phone)))
    return digits if 10 <= len(digits) <= 11 else None

def enrich_number(phone):
    try:
        response = requests.get(BASE_URL, params={
            'access_key': API_KEY,
            'number': phone,
            'country_code': 'US',
            'format': 1
        })
        data = response.json()
        return {
            'Phone': phone,
            'Valid': data.get('valid'),
            'Line Type': data.get('line_type'),
            'Carrier': data.get('carrier'),
            'Location': data.get('location'),
            'International Format': data.get('international_format')
        }
    except Exception as e:
        return {'Phone': phone, 'Error': str(e)}

st.title("📞 Phone Number Enrichment Tool")
st.write("Upload an Excel file with phone numbers to identify type and working status using Numverify.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    phone_columns = [col for col in df.columns if 'phone' in col.lower()]

    if not phone_columns:
        st.warning("No phone number columns detected.")
    else:
        st.success(f"Found phone columns: {', '.join(phone_columns)}")
        raw_phones = df[phone_columns].values.flatten()
        normalized = pd.Series(raw_phones).dropna().map(normalize_phone_number).dropna().drop_duplicates()

        st.write(f"Processing {len(normalized)} unique phone numbers...")

        enriched_data = []
        progress = st.progress(0)
        for i, phone in enumerate(normalized):
            enriched_data.append(enrich_number(phone))
            progress.progress((i + 1) / len(normalized))
            time.sleep(1)  # Rate limit safety

        result_df = pd.DataFrame(enriched_data)
        st.dataframe(result_df)

        st.download_button(
            label="📥 Download Enriched Results",
            data=result_df.to_csv(index=False).encode('utf-8'),
            file_name="enriched_phone_numbers.csv",
            mime='text/csv'
        )
