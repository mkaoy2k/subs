"""
User Management Page

This page provides user management functionality including:
- Viewing table structures
- Adding/removing columns
- Managing tables
"""
import streamlit as st
import pandas as pd
import db_utils as dbm
from admin_ui import show_admin_sidebar, init_session_state
from context_utils import init_context, update_context

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def show_page():
    # Show admin sidebar
    show_admin_sidebar()
    context = st.session_state.get('app_context', init_context())
    
    # --- manage users --- from here
    st.title("User Table Management")
    try:
        st.markdown("---")
        st.subheader("Query Subscribers")
        df = pd.DataFrame()
        btn11, btn12, btn13, btn14 = st.columns([5,5,5,5])
        info1, info2, info3 = st.columns([18,1,1])
        with btn11:
            if st.button("Active"):
                users = dbm.get_subscribers(state="active")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} active subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No active subscribers found")    
        with btn12:
            if st.button("Inactive"):
                users = dbm.get_subscribers(state="inactive")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} inactive subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No inactive subscribers found")
        with btn13:
            if st.button("Pending"):
                users = dbm.get_subscribers(state="pending")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} pending subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No pending subscribers found") 
                        
        with btn14:
            if st.button("All"):
                users = dbm.get_subscribers('all')
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"Retrieved {len(users)} subscribers")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info("No subscribers found")
    
        # --- manage a specific user --- from here
        st.markdown("---")
        st.subheader("Manage User")
        # Create three columns for better layout
        col1, col2, col3 = st.columns([5,5,5])
        with col1:
            email = st.text_input(':blue[Email:]', 
                        value=context.get('default_email', 'mkaoy2k@gmail.com'))
            email = email.strip()
        with col2:
            lang_list = dbm.get_article_languages()
            l10n = st.selectbox("Language:", 
                                lang_list,
                                index=0 if not context.get('language') else lang_list.index(context.get('language'))
                                )
        with col3:
            user_id = st.number_input("User ID:",
                                  min_value=1,
                                  max_value=100000,
                                  value=1)
        if st.button("Query"):
            user = dbm.get_subscriber(email)
            if user is not None:
                # Create a vertical display of user data
                st.write("### User Details")
                # Create three columns for better layout
                col1, col2, col3 = st.columns([5,5,5])
                
                # Display user data in a vertical format
                for i, (key, value) in enumerate(user.items()):
                    # Convert timestamp to local time if needed
                    if key in ['created_at', 'updated_at'] and value is not None:
                        value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                    # Alternate between columns for better space usage
                    if i % 3 == 0:
                        col1.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    elif i % 3 == 1:
                        col2.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    else:
                        col3.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:            
                st.warning(f"Email '{email}' not found")
    
        btn21, btn22, btn23, btn24 = st.columns([5,5,5,5])
    
        with btn22:
            if st.button("Subscribe"):
                if dbm.add_subscriber(email, "token", lang=l10n):
                    update_context({'language': l10n})
                    st.info(f"Subscribed {email} successfully")
                else:
                    st.warning(f"Failed to subscribe {email}")
    
        with btn23:
            if st.button("Unsubscribe"):
                if dbm.remove_subscriber(email):
                    st.info(f"Unsubscribed {email} successfully")
                else:
                    st.warning(f"Failed to unsubscribe {email}")
    
        with btn21:
            if st.button("Delete by email"):
                if dbm.delete_subscriber(email):
                    st.info(f"Deleted {email} successfully")
                else:
                    st.warning(f"Failed to delete {email}")
        
        with btn24:
            if st.button("Delete by ID"):
                if dbm.delete_user(user_id):
                    st.info(f"Deleted {user_id} successfully")
                else:
                    st.warning(f"Failed to delete {user_id}")
    except Exception as err:
        st.error(f"An error occurred: {str(err)}")

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
else:
    show_page()
