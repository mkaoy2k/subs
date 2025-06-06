"""
資料庫查詢介面 (Database Query Interface)

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
3. 執行方式: streamlit run ops_db_query.py
"""

import streamlit as st
import pandas as pd  # pip install pandas
import db_utils as dbm

st.title("Query User Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    ---
    """
    )

df = pd.DataFrame()
btn1, btn2, btn3 = st.columns([2,2,2])

try:
    with btn1:
        if st.button("Active Subscribers"):
            users = dbm.get_subscribers()
            # keys as columns
            df = pd.DataFrame.from_dict(users, orient='columns')
            st.write(df)    
    with btn3:
        if st.button("Inactive Subscribers"):
            users = dbm.get_subscribers(status='inactive')
            df = pd.DataFrame.from_dict(users, orient='columns')
            st.write(df)    
    with btn2:
        if st.button("All Subscribers"):
            users = dbm.get_subscribers(status='both')
            df = pd.DataFrame.from_dict(users, orient='columns')
            st.write(df)
                
    # --- query a specific user --- from here
    email = st.text_input(':blue[Email:]', 
                    placeholder='Enter email to Query')
    if st.button("User Query"):
        user = dbm.get_user(email)
        if user is not None:
            st.write(user)
            # keys as indeces
            df = pd.DataFrame.from_dict(user, orient='index')  
            st.write(df)          
        else:            
            st.info(f"Email='{email}' not found")
except Exception as err:
    st.info(f"Caught '{err}'. class is {type(err)}")
