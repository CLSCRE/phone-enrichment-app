import pandas as pd
import streamlit as st

def format_to_e164(phone):
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 10:
        return "+1" + phone
    elif len(phone) == 11 and phone.startswith("1"):
        return "+" + phone
    elif phone.startswith("+") and len(phone) > 10:
        return phone
    return None

st.title("Multi-Column Phone Extractor & Formatter for Twilio Lookup")

uploaded_file = st.file_uploader("Upload Excel File with Phone Numbers", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Find all phone-related columns (case-insensitive match)
    phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'cell' in col.lower() or 'mobile' in col.lower()]
    
    if not phone_cols:
        st.warning("No phone-related columns found.")
    else:
        st.write(f"Found phone columns: {phone_cols}")

        # Combine all phone number columns into one Series
        phone_series = pd.concat([df[col] for col in phone_cols], ignore_index=True)

        # Drop blanks, format to E.164, and drop invalids
        phone_series = phone_series.dropna().astype(str)
        phone_series = phone_series.map(format_to_e164).dropna().drop_duplicates().reset_index(drop=True)

        # Final DataFrame
        formatted_df = pd.DataFrame({'E164 Phone': phone_series})

        st.write("📋 Preview of formatted phone numbers:", formatted_df.head())

        csv = formatted_df.to_csv(index=False)
        st.download_button("📥 Download CSV for Twilio", csv, "Formatted_Phone_List_For_Twilio.csv", "text/csv")
