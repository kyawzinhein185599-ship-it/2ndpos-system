import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json

# (၁) Page Config & CSS
st.set_page_config(page_title="Premium POS", page_icon="📊", layout="centered")
st.markdown("""
    <style>
    .income-text { color: #1e7e34; font-weight: bold; font-size: 26px;}
    .expense-text { color: #dc3545; font-weight: bold; font-size: 26px;}
    .balance-text { color: #007bff; font-weight: bold; font-size: 26px;}
    .step-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #007bff; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

# 🇲🇲 မြန်မာဂဏန်းများကို အင်္ဂလိပ်ဂဏန်းသို့ ပြောင်းပေးသော စနစ်
def convert_myanmar_numerals(text):
    if not isinstance(text, str):
        text = str(text)
    mm_digits = '၀၁၂၃၄၅၆၇၈၉'
    en_digits = '0123456789'
    table = str.maketrans(mm_digits, en_digits)
    return text.translate(table)

# (၂) Google Sheet ချိတ်ဆက်ခြင်း Function
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["gcp_json"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

# ⚠️ သင့် Google Sheet နာမည်
SHEET_NAME = "POS_Data"

# (၃) Password Check
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password (စကားဝှက်) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password (စကားဝှက်) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        st.error("Password မှားနေပါသည်။")
        return False
    return True

# (၄) Main POS System
if check_password():
    st.title("📊 Premium POS & ငွေစာရင်းစနစ်")
    
    # စာရင်းသွင်းပြီးကြောင်း Message ပြသရန် 
    if 'flash_msg' in st.session_state:
        st.success(st.session_state['flash_msg'])
        del st.session_state['flash_msg']
    
    try:
        client = init_connection()
        sheet = client.open(SHEET_NAME).sheet1
        
        # Data ကို ချက်ချင်းဆွဲယူခြင်း
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        with st.form("pos_form", clear_on_submit=True):
            st.subheader("📝 စာရင်းအသစ်သွင်းရန်")
            col1, col2 = st.columns(2)
            with col1:
                trans_date = st.date_input("ရက်စွဲ", date.today())
                trans_type = st.selectbox("အမျိုးအစား", ["ဝင်ငွေ", "ထွက်ငွေ"])
                account = st.selectbox("အကောင့် / နေရာ", ["Cash", "Kpay", "Bank 1", "Bank 2", "ကိုရောင်နီ", "နေလင်းစိုး", "သက်အောင်လွင်", "ညီညီ"])
            with col2:
                desc = st.text_input("အကြောင်းအရာ")
                amount_str = st.text_input("ပမာဏ (ကျပ်)", value="0")
            
            submitted = st.form_submit_button("စာရင်းသွင်းမည်")
            
            if submitted:
                clean_str = convert_myanmar_numerals(amount_str).replace(',', '').strip()
                
                try:
                    amount = float(clean_str)
                    if amount > 0:
                        # Google Sheet သို့ Row အသစ် တစ်ကြောင်း ထည့်ခြင်း
                        row_data = [str(trans_date), trans_type, account, desc, amount]
                        sheet.append_row(row_data)
                        
                        # Message အား မှတ်သားပြီး ချက်ချင်း Refresh လုပ်ခြင်း
                        st.session_state['flash_msg'] = f"✅ {trans_type} {amount:,.0f} ကျပ် စာရင်းသွင်းပြီးပါပြီ!"
                        st.rerun()
                    else:
                        st.error("❌ ပမာဏသည် 0 ထက် ကြီးရပါမည်။")
                        
                except ValueError:
                    st.error("❌ ကျေးဇူးပြု၍ ပမာဏကို ဂဏန်းဖြင့်သာ မှန်ကန်စွာ ရိုက်ထည့်ပါ။")

        # (၅) အကျဉ်းချုပ် Dashboard ပြသခြင်း
        if not df.empty:
            df['ပမာဏ'] = pd.to_numeric(df['ပမာဏ'], errors='coerce').fillna(0)
            
            total_income = df[df['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
            total_expense = df[df['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
            system_total_balance = total_income - total_expense
            
            st.markdown("---")
            st.subheader("💰 ယနေ့ အကျဉ်းချုပ်")
            
            colA, colB, colC = st.columns(3)
            with colA:
                st.markdown(f"**စုစုပေါင်း ဝင်ငွေ**<br><span class='income-text'>+ {total_income:,.0f} Ks</span>", unsafe_allow_html=True)
            with colB:
                st.markdown(f"**စုစုပေါင်း ထွက်ငွေ**<br><span class='expense-text'>- {total_expense:,.0f} Ks</span>", unsafe_allow_html=True)
            with colC:
                balance_color = "income-text" if system_total_balance >= 0 else "expense-text"
                st.markdown(f"**ကွန်ပျူတာရှိငွေ (Total)**<br><span class='{balance_color}'>{system_total_balance:,.0f} Ks</span>", unsafe_allow_html=True)
            
            # (၆) အကြွေးစာရင်း ဇယား
            st.markdown("---")
            st.subheader("👥 အကြွေးစာရင်း အကျဉ်းချုပ်")
            
            debt_list = []
            people = ["ကိုရောင်နီ", "နေလင်းစိုး", "သက်အောင်လွင်", "ညီညီ"]
            for p in people:
                person_df = df[df['အကောင့်'] == p]
                lent = person_df[person_df['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
                repaid = person_df[person_df['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
                debt = lent - repaid
                debt_list.append({'အမည်': p, 'ရရန်ရှိသော အကြွေး (Ks)': debt})
                
            debt_df = pd.DataFrame(debt_list)
            total_debt = debt_df['ရရန်ရှိသော အကြွေး (Ks)'].sum()
            
            def style_debt(row):
                if row['ရရန်ရှိသော အကြွေး (Ks)'] > 0:
                    return ['background-color: #ffcccc; color: #cc0000; font-weight: bold'] * len(row)
                elif row['ရရန်ရှိသော အကြွေး (Ks)'] < 0
