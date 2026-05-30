import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json
import time

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

def get_data(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

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
    
    try:
        client = init_connection()
        sheet = client.open(SHEET_NAME).sheet1

        # 🌟 ချက်ချင်း Update ဖြစ်ကြောင်း ပြသရန် (Flash Message)
        if 'flash' in st.session_state:
            flash_msg = st.session_state['flash']['msg']
            flash_type = st.session_state['flash']['type']
            
            if flash_type == "ဝင်ငွေ":
                st.markdown(f"""
                <div style="background-color: #d4edda; border-left: 6px solid #28a745; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="color: #155724; margin: 0;">✅ {flash_msg}</h4>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f8d7da; border-left: 6px solid #dc3545; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="color: #721c24; margin: 0;">🔻 {flash_msg}</h4>
                </div>
                """, unsafe_allow_html=True)
            del st.session_state['flash']

        # 🌟 အဆင့် (၁) - စာရင်းသွင်းရန် ဖောင်
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
                    row_data = [str(trans_date), trans_type, account, desc, amount]
                    sheet.insert_row(row_data, index=2)
                    
                    st.session_state['flash'] = {
                        'msg': f"{trans_type} {amount:,.0f} ကျပ် အောင်မြင်စွာ စာရင်းသွင်းပြီးပါပြီ!",
                        'type': trans_type
                    }
                    time.sleep(1)
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()
                else:
                    st.error("❌ ပမာဏသည် 0 ထက် ကြီးရပါမည်။")
            except ValueError:
                st.error("❌ ကျေးဇူးပြု၍ ပမာဏကို ဂဏန်းဖြင့်သာ မှန်ကန်စွာ ရိုက်ထည့်ပါ။")

        # 🌟 Data အသစ်များကို ချက်ချင်း ပြန်ဖတ်မည်
        df = get_data(sheet)

        # 🌟 App အဖွင့်တွင် သိမ်းဆည်းထားသော "ပြင်ပလက်ကျန်ငွေ" ကို Google Sheet မှ လှမ်းဖတ်မည်
        if 'saved_balances_fetched' not in st.session_state:
            try:
                settings_ws = client.open(SHEET_NAME).worksheet("Saved_Balances")
                st.session_state['saved_actual'] = settings_ws.acell('B2').value
            except Exception:
                # Worksheet မရှိသေးပါက အလိုအလျောက် အသစ်ဖန်တီးပေးမည်
                settings_ws = client.open(SHEET_NAME).add_worksheet(title="Saved_Balances", rows=5, cols=2)
                settings_ws.update_acell('A1', "Computer Balance (Auto)")
                settings_ws.update_acell('A2', "Actual Cash")
                st.session_state['saved_actual'] = "0"
            
            st.session_state['saved_balances_fetched'] = True

        if not df.empty:
            df['ပမာဏ'] = pd.to_numeric(df['ပမာဏ'], errors='coerce').fillna(0)
            
            # (၅) ယနေ့ အကျဉ်းချုပ် တွက်ချက်ခြင်း (စာရင်းဝင်သမျှ အားလုံးကို အတိအကျ ပေါင်းပြမည်)
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
                st.markdown(f"**ကွန်ပျူတာရှိငွေ စုစုပေါင်း**<br><span class='{balance_color}'>{system_total_balance:,.0f} Ks</span>", unsafe_allow_html=True)
            
            # (၆) အကြွေးစာရင်း ဇယား (လူ ၄ ယောက်)
            st.markdown("---")
            st.subheader("👥 အကြွေးစာရင်း အကျဉ်းချုပ်")
            debt_list = []
            people = ["ကိုရောင်နီ", "နေလင်းစိုး", "သက်အောင်လွင်", "ညီညီ"]
            for p in people:
                person_df = df[df['အကောင့်'] == p]
                lent = person_df[person_df['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
                repaid = person_df[person_df['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
                debt_list.append({'အမည်': p, 'ရရန်ရှိသော အကြွေး (Ks)': lent - repaid})
                
            debt_df = pd.DataFrame(debt_list)
            total_debt = debt_df['ရရန်ရှိသော အကြွေး (Ks)'].sum()
            
            def style_debt(row):
                if row['ရရန်ရှိသော အကြွေး (Ks)'] > 0:
                    return ['background-color: #ffcccc; color: #cc0000; font-weight: bold'] * len(row)
                elif row['ရရန်ရှိသော အကြွေး (Ks)'] < 0:
                    return ['background-color: #ccffcc; color: #006600; font-weight: bold'] * len(row)
                return ['background-color: #e6f2ff; color: #004080; font-weight: bold'] * len(row)
            
            st.dataframe(debt_df.style.apply(style_debt, axis=1).format({'ရရန်ရှိသော အကြွေး (Ks)': "{:,.0f}"}), use_container_width=True)

            # (၇) ဘဏ် နှင့် Kpay စာရင်း ဇယား
            st.markdown("---")
            st.subheader("🏦 ဘဏ် နှင့် Kpay လက်ကျန်စာရင်း")
            bank_list = []
            for b in ["Kpay", "Bank 1", "Bank 2"]:
                bank_df_temp = df[df['အကောင့်'] == b]
                b_in = bank_df_temp[bank_df_temp['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
                b_out = bank_df_temp[bank_df_temp['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
                bank_list.append({'ဘဏ် / အကောင့်': b, 'လက်ကျန်ငွေ (Ks)': b_in - b_out})
                
            bank_table_df = pd.DataFrame(bank_list)
            total_bank = bank_table_df['လက်ကျန်ငွေ (Ks)'].sum()
            
            def style_bank(row):
                if row['လက်ကျန်ငွေ (Ks)'] > 0:
                    return ['background-color: #e6ffe6; color: #004d00; font-weight: bold'] * len(row)
                elif row['လက်ကျန်ငွေ (Ks)'] < 0:
                    return ['background-color: #ffe6e6; color: #800000; font-weight: bold'] * len(row)
                return ['background-color: #f8f9fa; color: #6c757d; font-weight: bold'] * len(row)
                
            st.dataframe(bank_table_df.style.apply(style_bank, axis=1).format({'လက်ကျန်ငွေ (Ks)': "{:,.0f}"}), use_container_width=True)

            # 🌟 (၈) စာရင်းချုပ် တိုက်ဆိုင်စစ်ဆေးခြင်း (Math တွက်ချက်မှု အသေအချာ ပြင်ဆင်ထားသည်)
            st.markdown("---")
            st.subheader("⚖️ စာရင်းချုပ် တိုက်ဆိုင်စစ်ဆေးခြင်း")
            
            # စာရင်းချုပ်ရန်အတွက် "အသားတင် ပိုင်ဆိုင်မှု (Total Assets)" ကို တွက်ချက်ခြင်း 
            # (အကြွေးပေး/ဆပ် ခြင်းသည် ပိုင်ဆိုင်မှုကို မပြောင်းလဲစေသောကြောင့် ၎င်းတို့ကို ဖယ်ထုတ်တွက်ချက်ပါသည်)
            real_df = df[~df['အကောင့်'].isin(people)]
            real_income = real_df[real_df['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
            real_expense = real_df[real_df['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
            total_assets = real_income - real_expense

            def update_actual_cash():
                val = str(st.session_state['actual_cash_widget']).replace(',', '').strip()
                st.session_state['saved_actual'] = val if val else "0"

            # ကွန်ပျူတာရှိငွေကို Auto တွက်ထားသော Total Assets ဖြင့် အမြဲပြသမည်
            default_comp = f"{int(total_assets):,.0f}"
                
            try:
                raw_actual = str(st.session_state['saved_actual']).replace(',', '').strip() if st.session_state['saved_actual'] else "0"
                default_actual = f"{float(raw_actual):,.0f}"
            except:
                default_actual = "0"

            col_x, col_y = st.columns(2)
            with col_x:
                # ဤအကွက်သည် အကြွေးများကိုပါ ထည့်သွင်းစဉ်းစားထားသောကြောင့် အကျဉ်းချုပ်ဇယားမှ Balance နှင့် ကွာခြားနိုင်သည်
                comp_bal_str = st.text_input("💻 ကွန်ပျူတာရှိ စာရင်းရှိငွေ (Auto)", value=default_comp)
            with col_y:
                actual_cash_str = st.text_input("🖐️ လက်ကျန်ငွေသား (ပြင်ပရှိအမှန်တကယ်ငွေ)", 
                                                value=default_actual, 
                                                key="actual_cash_widget",
                                                on_change=update_actual_cash)
                
            clean_comp_bal = convert_myanmar_numerals(comp_bal_str).replace(',', '').strip()
            clean_actual_cash = convert_myanmar_numerals(actual_cash_str).replace(',', '').strip()
            
            if clean_comp_bal == "": clean_comp_bal = "0"
            if clean_actual_cash == "": clean_actual_cash = "0"
            
            # 🌟 ပြင်ပလက်ကျန်ငွေ ကိုသာ အမြဲတမ်းမှတ်သားပေးမည့် Save Button
            if st.button("💾 ပြင်ပလက်ကျန်ငွေ (Actual Cash) ကို အမြဲတမ်းမှတ်သားမည်"):
                try:
                    settings_ws = client.open(SHEET_NAME).worksheet("Saved_Balances")
                    settings_ws.update_acell('B2', clean_actual_cash)
                    
                    st.session_state['saved_actual'] = clean_actual_cash
                    st.success("✅ အောင်မြင်စွာ မှတ်သားပြီးပါပြီ! App ပိတ်ပြီး ပြန်ဖွင့်လျှင်လည်း ဤဂဏန်းအတိုင်း ပြသပါမည်။")
                    time.sleep(1.5)
                    try:
                        st.rerun()
                    except AttributeError:
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Save လုပ်ရာတွင် အခက်အခဲရှိနေပါသည် - {e}")

            try:
                comp_bal = float(clean_comp_bal)
                actual_cash = float(clean_actual_cash)
                
                # လူကြီးမင်း တောင်းဆိုထားသည့်အတိုင်း တွက်ချက်မှု အဆင့် (၃) ဆင့်
                step_1 = comp_bal - actual_cash
                step_2 = step_1 - total_debt
                final_variance = step_2 - total_bank
                
                st.markdown(f"""
                <div class="step-box">
                    <b style="font-size: 18px;">တွက်ချက်မှု အဆင့်ဆင့်:</b><br><br>
                    🔹 <b>အဆင့် ၁:</b> ကွန်ပျူတာရှိငွေ ({comp_bal:,.0f}) မှ ပြင်ပလက်ကျန်ငွေ ({actual_cash:,.0f}) ကိုနှုတ်ခြင်း<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;ရလဒ် = <b>{step_1:,.0f} Ks</b><br><br>
                    🔹 <b>အဆင့် ၂:</b> ရလဒ် ({step_1:,.0f}) မှ လူ(၄)ယောက်၏ အကြွေးစုစုပေါင်း ({total_debt:,.0f}) ကိုထပ်နှုတ်ခြင်း<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;ရလဒ် = <b>{step_2:,.0f} Ks</b><br><br>
                    🔹 <b>အဆင့် ၃:</b> ရလဒ် ({step_2:,.0f}) မှ (Kpay+ဘဏ်၁+ဘဏ်၂) စုစုပေါင်း ({total_bank:,.0f}) ကိုထပ်နှုတ်ခြင်း<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;နောက်ဆုံး ကွာခြားချက် = <b style="color: {'#1e7e34' if final_variance == 0 else '#dc3545'}; font-size: 20px;">{final_variance:,.0f} Ks</b>
                </div>
                """, unsafe_allow_html=True)
                
                if final_variance == 0:
                    st.success("✅ စာရင်းအားလုံး တိကျစွာ ကိုက်ညီပါသည်။ (ကွာခြားချက်မရှိပါ)")
                elif final_variance > 0:
                    st.error(f"🔻 စာရင်းမကိုက်ပါ။ {final_variance:,.0f} ကျပ် လိုနေပါသည် (ငွေလိုနေသည်)။")
                else:
                    st.warning(f"⚠️ စာရင်းမကိုက်ပါ။ {abs(final_variance):,.0f} ကျပ် ပိုနေပါသည် (ငွေပိုနေသည်)။")
                        
            except ValueError:
                st.error("ဂဏန်းများကို မှန်ကန်စွာ ရိုက်ထည့်ပါ။")

            # (၉) နေ့စဉ်မှတ်တမ်း ဇယား
            st.markdown("---")
            st.subheader("📋 နေ့စဉ် မှတ်တမ်းများ")
            def highlight_rows(row):
                if row['အမျိုးအစား'] == 'ဝင်ငွေ': return ['background-color: #e6ffe6; color: #004d00'] * len(row)
                if row['အမျိုးအစား'] == 'ထွက်ငွေ': return ['background-color: #ffe6e6; color: #800000'] * len(row)
                return [''] * len(row)
            
            st.dataframe(df.style.apply(highlight_rows, axis=1).format({"ပမာဏ": "{:,.0f}"}), use_container_width=True)

    except Exception as e:
        st.error(f"Google Sheet နှင့် ချိတ်ဆက်ရာတွင် အခက်အခဲရှိနေပါသည်။ Error: {e}")
