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

    if "Phone" not in df.columns:
        st.error("Your file must contain a 'Phone' column.")
        st.stop()

    # Format to E.164
    df["Formatted"] = df["Phone"].astype(str).apply(format_to_e164)

    # Validate with Twilio and blank out invalid ones
    cleaned = []
    with st.spinner("Validating phone numbers via Twilio..."):
        for phone in df["Formatted"]:
            cleaned.append(validate_with_twilio(phone, account_sid, auth_token))
            sleep(0.5)  # To respect Twilio rate limits

    df["Phone"] = cleaned
    df.drop(columns=["Formatted"], inplace=True)

    st.success("Phone numbers cleaned successfully!")
    st.dataframe(df.head())

    csv = df.to_csv(index=False)
    st.download_button("📥 Download Cleaned CSV", csv, "Twilio_Cleaned_Phone_List.csv", "text/csv")
