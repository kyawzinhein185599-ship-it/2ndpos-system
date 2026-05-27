import streamlit as st
import pandas as pd
from datetime import date

# (၁) စာမျက်နှာကို Premium ပုံစံဖြစ်စေရန် ပြင်ဆင်ခြင်း
st.set_page_config(page_title="Premium POS", page_icon="📊", layout="centered")

# Custom CSS ဖြင့် အရောင်များ သတ်မှတ်ခြင်း
st.markdown("""
    <style>
    .income-text { color: #1e7e34; font-weight: bold; font-size: 26px;}
    .expense-text { color: #dc3545; font-weight: bold; font-size: 26px;}
    .balance-text { color: #007bff; font-weight: bold; font-size: 26px;}
    </style>
""", unsafe_allow_html=True)

# (၂) Password စစ်ဆေးသည့် စနစ်
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Password မှန်ရင် ဖျက်ထားမယ်
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password (စကားဝှက်) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password (စကားဝှက်) ရိုက်ထည့်ပါ", type="password", on_change=password_entered, key="password")
        st.error("Password မှားနေပါသည်။ ပြန်လည်ကြိုးစားပါ။")
        return False
    return True

# Password မှန်ကန်မှသာ အောက်ပါ POS စနစ်ကို ပြသမည်
if check_password():
    st.title("📊 Premium POS & ငွေစာရင်းစနစ်")
    
    # Session state တွင် Data သိမ်းရန် နေရာလုပ်ခြင်း
    if 'data' not in st.session_state:
        st.session_state['data'] = pd.DataFrame(columns=['ရက်စွဲ', 'အမျိုးအစား', 'အကောင့်', 'အကြောင်းအရာ', 'ပမာဏ'])

    # (၃) နေ့စဉ် စာရင်းသွင်းရန် Form
    with st.form("pos_form", clear_on_submit=True):
        st.subheader("📝 စာရင်းအသစ်သွင်းရန်")
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("ရက်စွဲ", date.today())
            trans_type = st.selectbox("အမျိုးအစား", ["ဝင်ငွေ", "ထွက်ငွေ"])
            account = st.selectbox("အကောင့် / နေရာ", ["Cash", "Kpay", "Bank 1", "Bank 2", "လူ (၁)", "လူ (၂)", "လူ (၃)", "လူ (၄)"])
        with col2:
            desc = st.text_input("အကြောင်းအရာ")
            amount = st.number_input("ပမာဏ (ကျပ်)", min_value=0.0, step=1000.0)
        
        submitted = st.form_submit_button("စာရင်းသွင်းမည်")
        
        if submitted:
            new_data = pd.DataFrame({
                'ရက်စွဲ': [trans_date],
                'အမျိုးအစား': [trans_type],
                'အကောင့်': [account],
                'အကြောင်းအရာ': [desc],
                'ပမာဏ': [amount]
            })
            st.session_state['data'] = pd.concat([st.session_state['data'], new_data], ignore_index=True)
            
            # ဝင်ငွေ၊ ထွက်ငွေ အလိုက် Message အရောင်ခွဲပြခြင်း
            if trans_type == "ဝင်ငွေ":
                st.success(f"✅ ဝင်ငွေ {amount:,.0f} ကျပ် စာရင်းသွင်းပြီးပါပြီ!")
            else:
                st.error(f"🔻 ထွက်ငွေ {amount:,.0f} ကျပ် စာရင်းသွင်းပြီးပါပြီ!")

    # (၄) အကျဉ်းချုပ် (Dashboard) တွက်ချက်ခြင်း
    df = st.session_state['data']
    if not df.empty:
        total_income = df[df['အမျိုးအစား'] == 'ဝင်ငွေ']['ပမာဏ'].sum()
        total_expense = df[df['အမျိုးအစား'] == 'ထွက်ငွေ']['ပမာဏ'].sum()
        balance = total_income - total_expense
        
        st.markdown("---")
        st.subheader("💰 ယနေ့ အကျဉ်းချုပ်")
        
        # HTML ဖြင့် အရောင်လှလှလေး ပေါ်အောင်ရေးထားခြင်း
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(f"**စုစုပေါင်း ဝင်ငွေ**<br><span class='income-text'>+ {total_income:,.0f} Ks</span>", unsafe_allow_html=True)
        with colB:
            st.markdown(f"**စုစုပေါင်း ထွက်ငွေ**<br><span class='expense-text'>- {total_expense:,.0f} Ks</span>", unsafe_allow_html=True)
        with colC:
            balance_color = "income-text" if balance >= 0 else "expense-text"
            st.markdown(f"**လက်ကျန်ငွေ**<br><span class='{balance_color}'>{balance:,.0f} Ks</span>", unsafe_allow_html=True)
        
        # ဇယားကွက်ကို ဝင်ငွေ/ထွက်ငွေ အလိုက် အရောင်ချယ်ခြင်း (Pandas Styling)
        st.markdown("---")
        st.subheader("📋 မှတ်တမ်းများ")
        
        def highlight_rows(row):
            if row['အမျိုးအစား'] == 'ဝင်ငွေ':
                return ['background-color: #e6ffe6; color: #004d00'] * len(row) # အစိမ်းနုရောင်
            elif row['အမျိုးအစား'] == 'ထွက်ငွေ':
                return ['background-color: #ffe6e6; color: #800000'] * len(row) # အနီနုရောင်
            return [''] * len(row)
        
        # ဇယားကို အရောင်ထည့်ပြီး ပမာဏကို ကော်မာခံပြသခြင်း
        styled_df = df.style.apply(highlight_rows, axis=1).format({"ပမာဏ": "{:,.0f}"})
        st.dataframe(styled_df, use_container_width=True)
