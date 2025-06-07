"""
資料庫更新介面 (Database Update Interface)

此模組提供一個基於 Streamlit 的網頁介面，
用於查詢和管理訂閱者資料庫。

主要功能:
- 顯示活躍訂閱者清單
- 顯示非活躍訂閱者清單
- 顯示所有訂閱者資料
- 支援電子郵件查詢特定用戶

使用技術:
- Streamlit: 網頁介面框架
- Pandas: 資料處理與顯示
- db_utils: 自訂資料庫工具模組

注意事項:
1. 需先設定好環境變數 (.env 檔案)
2. 需要安裝相關套件: streamlit, pandas
3. 執行方式: streamlit run ops_db_update.py
"""

import streamlit as st
import pandas as pd  # pip install pandas
import db_utils as dbm
from email_utils import validate_email

st.title("Update User Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    """
    )

df = pd.DataFrame()
btn1, btn2 = st.columns([5,5])

try:
    with btn1:
        if st.button("Active Subscribers"):
            users = dbm.get_subscribers(state='active')
            if users:
                # Create DataFrame with explicit dtype for each column
                df = pd.DataFrame(users, columns=users[0].keys())
                # Convert timestamp columns to string for display
                for col in ['created_at', 'updated_at']:
                    if col in df.columns:
                        df[col] = df[col].astype(str)
                st.dataframe(df)  # Use st.dataframe instead of st.write for DataFrames
            else:
                st.info("No active subscribers found")    
    with btn2:
        if st.button("Inactive Subscribers"):
            users = dbm.get_subscribers(state='inactive')
            if users:
                df = pd.DataFrame(users, columns=users[0].keys())
                for col in ['created_at', 'updated_at']:
                    if col in df.columns:
                        df[col] = df[col].astype(str)
                st.dataframe(df)
            else:
                st.info("No inactive subscribers found")
    
    # --- query a specific user --- from here
    st.markdown(
    """
    ---
    """
    )
    email = st.text_input(':blue[Email:]', 
                    placeholder='Enter email to subscribe')
    email = email.strip()
    btn3, btn4 = st.columns([5,5])
    
    with btn3:
        if st.button("Subscribe"):
            if not validate_email(email):
                st.warning("Please enter a valid email address")
            else:
                dbm.add_subscriber(email, "token")  
                st.info("Subscribed successfully")
    
    with btn4:
        if st.button("Unsubscribe"):
            if not validate_email(email):
                st.warning("Please enter a valid email address")
            else:
                dbm.remove_subscriber(email)  
                st.info("Unsubscribed successfully")
except Exception as err:
    st.error(f"Caught '{err}'. class is {type(err)}")
