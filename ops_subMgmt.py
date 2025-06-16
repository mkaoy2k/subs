"""
Subscriber Table Update Interface

This module provides a Streamlit-based web interface
for querying and managing the subscriber database.

Main Features:
- Display active subscriber list
- Display inactive subscriber list
- Display all subscriber data
- Support email query for specific users

Technologies Used:
- Streamlit: Web interface framework
- Pandas: Data processing and display
- db_utils: Custom database utility module

Notes:
1. Environment variables must be set up (.env file)
2. Required packages: streamlit, pandas
3. Execution: streamlit run ops_user_update.py
"""

import streamlit as st
import pandas as pd  # pip install pandas
import db_utils as dbm
from email_utils import validate_email

st.title("Subscriber Table Management")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    """
    )

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

df = pd.DataFrame()
btn1, btn2, btn3 = st.columns([5,5,5])

try:
    with btn1:
        if st.button("Active"):
            users = dbm.get_subscribers(state='active')
            if users:
                df = pd.DataFrame(users, columns=users[0].keys())
                df = format_timestamps(df)
                st.dataframe(df)
            else:
                st.info("No active subscribers found")    
    with btn3:
        if st.button("Inactive"):
            users = dbm.get_subscribers(state='inactive')
            if users:
                df = pd.DataFrame(users, columns=users[0].keys())
                df = format_timestamps(df)
                st.dataframe(df)
            else:
                st.info("No inactive subscribers found")
    with btn2:
        if st.button("Pending"):
            users = dbm.get_subscribers(state='pending')
            if users:
                df = pd.DataFrame(users, columns=users[0].keys())
                df = format_timestamps(df)
                st.dataframe(df)
            else:
                st.info("No pending subscribers found")     
    
    # --- update a specific ubscriber --- from here
    st.markdown(
    """
    ---
    """
    )
    col1, col2 = st.columns([5,5])
    with col1:
        email = st.text_input(':blue[Email:]', 
                        placeholder='Enter email to Update')
        email = email.strip()
    with col2:
        l10n = st.selectbox("Language:", ["US", "繁中"], label_visibility="hidden")
    if st.button("Query"):
        if not validate_email(email):
            st.warning("Please enter a valid email address")
        else:
            user = dbm.get_subscriber(email)
            if user is not None:
                # Create a vertical display of user data
                st.write("### User Details")
                # Create two columns for better layout
                col1, col2 = st.columns(2)
                
                # Display user data in a vertical format
                for i, (key, value) in enumerate(user.items()):
                    # Convert timestamp to local time if needed
                    if key in ['created_at', 'updated_at'] and value is not None:
                        value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                    # Alternate between columns for better space usage
                    if i % 2 == 0:
                        col1.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    else:
                        col2.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:            
                st.warning(f"Email '{email}' not found")
    
    btn4, btn5, btn6 = st.columns([5,5,5])
    
    with btn4:
        if st.button("Subscribe"):
            if not validate_email(email):
                st.warning(f"{email} is not a valid email address")
            else:
                if dbm.add_subscriber(email, "token", lang=l10n):
                    st.info(f"Subscribed {email} successfully")
                else:
                    st.warning(f"Failed to subscribe {email}")
    
    with btn5:
        if st.button("Unsubscribe"):
            if not validate_email(email):
                st.warning(f"{email} is not a valid email address")
            else:
                if dbm.remove_subscriber(email):
                    st.info(f"Unsubscribed {email} successfully")
                else:
                    st.warning(f"Failed to unsubscribe {email}")
    
    with btn6:
        if st.button("Delete"):
            if not validate_email(email):
                st.warning(f"{email} is not a valid email address")
            else:
                if dbm.delete_subscriber(email):
                    st.info(f"Deleted {email} successfully")
                else:
                    st.warning(f"Failed to delete {email}") 
    
    # --- drop table --- from here
    st.markdown(
    """
    ---
    """
    )
    tbl = st.selectbox("Drop Table:", [dbm.user_tbl])
    if st.button("Drop Table"):
        dbm.drop_table(tbl)
        st.success(f"Dropped table: {tbl}")
except Exception as err:
    st.error(f"Caught '{err}'. class is {type(err)}")
