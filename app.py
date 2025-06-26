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

def twilio_lookup(phone, sid, token):
    try:
        url = f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}?type=carrier"
        response = requests.get(url, auth=(sid, token))
        if response.status_code == 200:
            data = response.json()
            return {
                "Phone": phone,
                "Phone Type": data.get("carrier", {}).get("type"),
                "Carrier": data.get("carrier", {}).get("name"),
                "Ported": data.get("carrier", {}).get("ported"),
            }
    except Exception:
        pass
    return {
        "Phone": phone,
        "Phone Type": None,
        "Carrier": None,
        "Ported": None,
    }

st.title("📞 Phone Number Enrichment with Twilio Lookup")

# Step 1: Upload Excel
uploaded_file = st.file_uploader("Upload Excel File with Phone Numbers", type=["xlsx"])

# Step 2: Enter Twilio credentials
sid = st.text_input("🔐 Twilio Account SID")
token = st.text_input("🔑 Twilio Auth Token", type="password")

if uploaded_file and sid and token:
    df = pd.read_excel(uploaded_file)

    # Step 3: Detect phone columns
    phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'cell' in col.lower() or 'mobile' in col.lower()]
    if not phone_cols:
        st.warning("No phone-related columns found.")
        st.stop()

    st.success(f"Found phone columns: {phone_cols}")

    # Step 4: Combine and format
    phone_series = pd.concat([df[col] for col in phone_cols], ignore_index=True)
    phone_series = phone_series.dropna().astype(str)
    phone_series = phone_series.map(format_to_e164).dropna().drop_duplicates().reset_index(drop=True)

    st.write("Preview of formatted numbers:", phone_series.head())

    # Step 5: Run Twilio Lookup
    results = []
    with st.spinner("🔍 Enriching phone numbers with Twilio..."):
        for phone in phone_series:
            results.append(twilio_lookup(phone, sid, token))
            sleep(0.5)  # To respect Twilio's rate limits

    enriched_df = pd.DataFrame(results)
    st.write("✅ Enrichment Complete. Preview:", enriched_df.head())

    csv = enriched_df.to_csv(index=False)
    st.download_button("📥 Download Enriched CSV", csv, "Twilio_Enriched_Phone_List.csv", "text/csv")
