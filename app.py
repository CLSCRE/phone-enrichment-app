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

def lookup_status(phone, sid, token):
    if not phone:
        return ("", "", "", "")
    url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?type=carrier"
    try:
        response = requests.get(url, auth=(sid, token))
        if response.status_code == 200:
            data = response.json()
            carrier = data.get("carrier", {}).get("name", "")
            phone_type = data.get("carrier", {}).get("type", "")
            ported = data.get("carrier", {}).get("ported", "")
            return (phone.replace("+1", ""), phone_type, carrier, ported)
    except:
        pass
    return ("", "", "", "")
    url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?type=carrier"
    try:
        response = requests.get(url, auth=(sid, token))
        if response.status_code == 200:
            data = response.json()
            carrier = data.get("carrier", {}).get("name", "")
            phone_type = data.get("carrier", {}).get("type", "")
            ported = data.get("carrier", {}).get("ported", "")
            return (phone.replace("+1", ""), phone_type, carrier, ported)
    except:
        pass
    return ("", "", "", "")

st.title("📞 Phone Number Cleaner & Status Lookup with Twilio")

uploaded_file = st.file_uploader("Upload CSV file with phone numbers", type=["csv"])
account_sid = st.text_input("🔐 Twilio Account SID")
auth_token = st.text_input("🔑 Twilio Auth Token", type="password")

if uploaded_file and account_sid and auth_token:
    df = pd.read_csv(uploaded_file)

    # Identify all phone-like columns
    phone_cols = [col for col in df.columns if 'phone' in col.lower()]

    if not phone_cols:
        st.error("No phone-related columns found in your file.")
        st.stop()

    st.success(f"Found phone columns: {phone_cols}")

    results = []
    for col in phone_cols:
        df[col] = df[col].astype(str).apply(format_to_e164)
        with st.spinner(f"Validating column '{col}' via Twilio..."):
            for phone in df[col]:
                formatted, phone_type, carrier, ported = lookup_status(phone, account_sid, auth_token)
                results.append({
                    "Original Column": col,
                    "Phone": formatted,
                    "Phone Type": phone_type,
                    "Carrier": carrier,
                    "Ported": ported
                })
                sleep(0.5)

    result_df = pd.DataFrame(results)
    st.write("📋 Detailed Phone Status Results:")
    st.dataframe(result_df.head(50))

    csv = result_df.to_csv(index=False)
    st.download_button("📥 Download Phone Status Report", csv, "Twilio_Phone_Status_Report.csv", "text/csv")
