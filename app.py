import streamlit as st
import pandas as pd
import requests
import time
from PIL import Image
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
import openpyxl
from openpyxl.styles import Font
import io

# --- SETUP PAGE AND LOGO EARLY ---
st.set_page_config(page_title="CLS CRE Phone Enrichment", layout="centered")
logo_path = "https://clscre.com/wp-content/uploads/2023/05/CLS-CRE_logo_white.png"
st.image(logo_path, width=400)
st.markdown("### Phone Number Cleaner - Numverify")

# --- LOGIN SETUP ---
config = yaml.safe_load("""
credentials:
  usernames:
    trevor@clscre.com:
      email: trevor@clscre.com
      name: Trevor Damyan
      password: '$2b$12$thrJtvf2t2gwuTwgjWqMDetotIh6WoVqQjhc9PQADuqzZYKu1sV12'

cookie:
  name: clscre_app
  key: clscre_token
  expiry_days: 1
""")
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
authenticator.login()

auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("Incorrect username or password")
elif auth_status is None:
    st.warning("Please enter your username and password")
elif auth_status:
    authenticator.logout("Logout", "sidebar")
    st.markdown("---")
    tabs = st.tabs(["Phone Cleaner", "Upload History"])
    username = st.session_state.get("username", "Unknown User")
    st.success(f"Welcome, {username}!")

    # --- MAIN APP ---
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
            line_type = data.get('line_type')
            valid = data.get('valid')
            working_score = "Low"
            if valid:
                if line_type == "mobile":
                    working_score = "High"
                elif line_type in ["landline", "voip"]:
                    working_score = "Medium"
            return {
                'Phone': phone,
                'Valid': valid,
                'Line Type': line_type,
                'Carrier': data.get('carrier'),
                'Location': data.get('location'),
                'Working Score': working_score
            }
        except Exception as e:
            return {'Phone': phone, 'Error': str(e)}

    st.markdown("#### Phone Number Enrichment Tool")
    st.caption("Upload a spreadsheet of phone numbers to identify type and working probability using Numverify.")

    with tabs[0]:
        uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        phone_columns = [col for col in df.columns if 'phone' in col.lower()]

        if not phone_columns:
            st.warning("No phone number columns detected.")
        else:
            st.success(f"Found phone columns: {', '.join(phone_columns)}")
            raw_phones = df[phone_columns].values.flatten()
            normalized = pd.Series(raw_phones).dropna().map(normalize_phone_number).dropna().drop_duplicates()

            st.write(f"Estimated valid phone numbers to scan: {len(normalized)}")
            enriched_data = []
            progress = st.progress(0)
            for i, phone in enumerate(normalized):
                enriched_data.append(enrich_number(phone))
                progress.progress((i + 1) / len(normalized))
                time.sleep(1)
            progress.empty()

            result_df = pd.DataFrame(enriched_data)

            # Filter out invalid numbers from original
            valid_phones = result_df[result_df["Valid"] == True]["Phone"].astype(str).str.replace(r"\D", "", regex=True)
            filtered_df = df.copy()

            # Save to Excel with formatting
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Original")
                result_df.to_excel(writer, index=False, sheet_name="Cleaned")

                # Apply green font to mobile rows in Original
                workbook = writer.book
                sheet = workbook["Original"]
                for i, phone in enumerate(filtered_df[phone_columns[0]].astype(str), start=2):
                    clean_phone = str(phone).strip().replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
                    match = result_df[result_df["Phone"] == clean_phone]
                    if not match.empty and match.iloc[0]["Line Type"] == "mobile":
                        for cell in sheet[i]:
                            cell.font = Font(color="008000")  # Green

            output.seek(0)
            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            upload_record = pd.DataFrame([{
                "Timestamp": timestamp,
                "Username": username,
                "Filename": uploaded_file.name,
                "Phones Scanned": len(normalized),
                "Valid": (result_df["Valid"] == True).sum(),
                "Mobile": (result_df["Line Type"] == "mobile").sum()
            }])
            try:
                existing = pd.read_csv("upload_history.csv")
                upload_record = pd.concat([existing, upload_record], ignore_index=True)
            except:
                pass
            upload_record.to_csv("upload_history.csv", index=False)

            st.download_button(
                label="📥 Download Excel with Cleaned Results (Sheet 2)",
                data=output,
                file_name="phone_enrichment_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.stop()

    with tabs[1]:
        try:
            history_df = pd.read_csv("upload_history.csv")
            history_df = history_df.sort_values("Timestamp", ascending=False)
            st.dataframe(history_df)
        except:
            st.info("No upload history found yet.")
