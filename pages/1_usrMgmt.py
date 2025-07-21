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
from subs_ui import show_admin_sidebar, init_session_state
from context_utils import init_context, update_context

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df


def show_user_update_page():
    """
    Display the user update interface with a form to update user information.
    """
    st.subheader("Manage Users")
    with st.container(border=True):    
        # Get user ID input
        user_id = st.number_input(
            "User ID to update:",
            min_value=1,
            value=1,
            step=1,
            help="Enter the ID of the user you want to update"
        )
        
        # Fetch current user data
        user = None
        if st.button("Load User Data"):
            with st.spinner("Loading user data..."):
                with getattr(dbm, 'get_db_connection')() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {dbm.db_tables['user']} WHERE id = ?", (user_id,))
                    result = cursor.fetchone()
                    if result:
                        user = dict(zip([col[0] for col in cursor.description], result))
                        st.session_state.current_user = user
                        st.success(f"Loaded user: {user.get('email', 'Unknown')}")
                    else:
                        st.error(f"User with ID {user_id} not found")
                        if 'current_user' in st.session_state:
                            del st.session_state.current_user
        
        # Display update form if user data is loaded
        if 'current_user' in st.session_state and st.session_state.current_user:
            user = st.session_state.current_user
            
            # Add custom CSS to make the form taller
            st.markdown("""
            <style>
                div[data-testid="stForm"] {
                    min-height: 500px;
                    padding: 20px;
                }
            </style>
            """, unsafe_allow_html=True)
            
            with st.form("update_user_form"):
                st.write("### Edit User Details")
                
                # Get available languages and current language from context
                context = st.session_state.get('app_context', {})
                available_languages = context.get('languages', ['US'])
                default_language = user.get('l10n', context.get('language', 'US'))
                
                # Create form fields with current values in a single row
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    email = st.text_input("Email", value=user.get('email', ''))
                    
                with col2:
                    # Get current state, default to 'active' if not set
                    current_state = user.get('is_active', 1)  # Default to active (1)
                    # Find the current state key from the value
                    current_state_key = next(
                        (k for k, v in dbm.Subscriber_State.items() if v == current_state),
                        'active'  # default key if not found
                    )
                    # Create selectbox with state options
                    selected_state = st.selectbox(
                        "Subscriber State",
                        options=list(dbm.Subscriber_State.keys()),
                        index=list(dbm.Subscriber_State.keys()).index(current_state_key)
                        if current_state_key in dbm.Subscriber_State else 0
                    )
                    # Store the numeric value of the selected state
                    is_active = dbm.Subscriber_State[selected_state]
                with col3:
                    l10n = st.selectbox(
                        "Language",
                        options=available_languages,
                        index=available_languages.index(default_language) if default_language in available_languages else 0,
                        key="l10n_select"
                    )
                
                # Submit button
                if st.form_submit_button(f"Update User ID: {user_id}"):
                    update_data = {
                        'email': email if email != user.get('email') else None,
                        'is_active': 1 if is_active else 0,
                        'l10n': l10n if l10n != user.get('l10n') else None
                    }
                    
                    # Remove None values
                    update_data = {k: v for k, v in update_data.items() if v is not None}
                    
                    if update_data:
                        if dbm.update_user(user_id, update_data):
                            st.success("User updated successfully!")
                            # Refresh the user data
                            if 'current_user' in st.session_state:
                                del st.session_state.current_user
                        else:
                            st.error("Failed to update user. Please check the logs for details.")
                    else:
                        st.warning("No changes detected.")
        
def show_subscriber_page():
    # Show admin sidebar
    show_admin_sidebar()
    context = st.session_state.get('app_context', init_context())
    
    # --- manage users --- from here
    with st.container(border=True):
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
    
        # Create three columns for better layout
        col1, col2, col3 = st.columns([5,5,5])
        with col1:
            email = st.text_input(':blue[Email:]', 
                        value=st.session_state.user_email)
            if email:  # Only call strip() if email is not None
                email = email.strip()
            else:
                email = ''  # Set default empty string if email is None
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
        if st.button("Query by email"):
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
        
        # --- manage a specific user --- from here
        st.subheader("Manage Subscribers")
        btn21, btn22 = st.columns([5,5])
    
        with btn21:
            if st.button(f"Subscribe: {email}"):
                user_data = {
                    'email': email,
                    'is_active': dbm.Subscriber_State['active'],
                    'token': 'token',
                    'l10n': l10n
                }
                if dbm.add_or_update_subscriber(user_data):
                    update_context({'language': l10n})
                    st.info(f"Subscribed {email} successfully")
                else:
                    st.warning(f"Failed to subscribe {email}")
    
        with btn22:
            if st.button(f"Unsubscribe: {email}"):
                if dbm.remove_subscriber(email):
                    st.info(f"Unsubscribed {email} successfully")
                else:
                    st.warning(f"Failed to unsubscribe {email}")
    
        with st.expander("Danger Zone", expanded=False):
            st.warning("⚠️ This action cannot be undone!")
            col221, col222 = st.columns([5,5])
            with col221:
                if st.button(f"Delete email: {email}"):
                    if dbm.delete_subscriber(email):
                        st.info(f"Deleted {email} successfully")
                    else:
                        st.warning(f"Failed to delete {email}")
            with col222:
                if st.button(f"Delete ID: {user_id}"):
                    if dbm.delete_user(user_id):
                        st.info(f"Deleted {user_id} successfully")
                    else:
                        st.warning(f"Failed to delete {user_id}")

def main():
    # Initialize session state
    init_session_state()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.switch_page("subs_ui.py")
    else:
        st.title("User Management")
        show_subscriber_page()
        show_user_update_page()

if __name__ == "__main__":
    main()
