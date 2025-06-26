import pandas as pd
import streamlit as st
import requests
from time import sleep

def format_to_e164(phone):
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 10:
        return "+1" + phone
    elif len(phone) == 11 and phone.startswith("1"):
        return "+" + phone
    elif phone.startswith("+") and len(phone) > 10:
        return phone
    return None

def validate_with_twilio(phone, sid, token):
    if not phone:
        return ""
    url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?type=carrier"
    try:
        response = requests.get(url, auth=(sid, token))
        if response.status_code == 200:
            return phone.replace("+1", "")  # Return cleaned US number
    except:
        pass
    return ""  # Blank out invalid or failed

st.title("📞 Phone Number Cleaner with Twilio Lookup")

uploaded_file = st.file_uploader("Upload CSV file with phone numbers", type=["csv"])
account_sid = st.text_input("🔐 Twilio Account SID")
auth_token = st.text_input("🔑 Twilio Auth Token", type="password")

if uploaded_file and account_sid and auth_token:
    df = pd.read_csv(uploaded_file)

    # Identify all phone-like columns
    phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'mobile' in col.lower() or 'cell' in col.lower()]

    if not phone_cols:
        st.error("No phone-related columns found in your file.")
        st.stop()

    st.success(f"Found phone columns: {phone_cols}")

    for col in phone_cols:
        df[col] = df[col].astype(str).apply(format_to_e164)
        cleaned = []
        with st.spinner(f"Validating column '{col}' via Twilio..."):
            for phone in df[col]:
                cleaned.append(validate_with_twilio(phone, account_sid, auth_token))
                sleep(0.5)
        df[col] = cleaned

    st.success("Phone numbers cleaned successfully!")
    st.dataframe(df.head())

    csv = df.to_csv(index=False)
    st.download_button("📥 Download Cleaned CSV", csv, "Twilio_Cleaned_Phone_List.csv", "text/csv")
