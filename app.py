import streamlit as st
import pandas as pd
import requests
import time
from PIL import Image
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader

# --- LOGIN SETUP ---
config = yaml.safe_load("""
credentials:
  usernames:
    trevor@clscre.com:
      email: trevor@clscre.com
      name: Trevor Damyan
      password: '$2b$12$hsm4K8BPvOHDd2YTXAgKZO4KMC9Ia2oZ8DWE3U4Vf49lXN5kk/IJq'

cookie:
  name: clscre_app
  key: clscre_token
  expiry_days: 1

preauthorized:
  emails: []
""")

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Incorrect username or password")
elif authentication_status is None:
    st.warning("Please enter your username and password")
elif authentication_status:
    authenticator.logout("Logout", "sidebar")

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
                'International Format': data.get('international_format'),
                'Working Score': working_score
            }
        except Exception as e:
            return {'Phone': phone, 'Error': str(e)}

    st.set_page_config(page_title="CLS CRE Phone Enrichment", layout="wide")
    logo_path = "https://clscre.com/wp-content/uploads/2023/05/CLS-CRE_logo_white.png"
    st.image(logo_path, width=200)

    st.title("📞 Phone Number Enrichment Tool")
    st.caption("Upload a spreadsheet of phone numbers to identify type and working probability using Numverify.")

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

            st.write(f"Processing {len(normalized)} unique phone numbers...")

            enriched_data = []
            progress = st.progress(0)
            for i, phone in enumerate(normalized):
                enriched_data.append(enrich_number(phone))
                progress.progress((i + 1) / len(normalized))
                time.sleep(1)

            result_df = pd.DataFrame(enriched_data)
            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Enriched Results as CSV",
                data=csv,
                file_name="enriched_phone_numbers.csv",
                mime='text/csv'
            )
