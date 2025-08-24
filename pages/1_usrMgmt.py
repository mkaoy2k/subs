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
from subs_ui import show_admin_sidebar
import context_utils as cu
import funcUtils as fu

def format_timestamps(df):
    """Convert timestamps to selected timezone and format.
    Handles various datetime formats and edge cases."""
    # Get timezone from context, default to 'America/Los_Angeles' if not set
    context = st.session_state.get('app_context', {})
    timezone = context.get('timezone', 'America/Los_Angeles')
    
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Convert to datetime, coercing errors to NaT
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Handle timezone conversion for valid timestamps
            mask = df[col].notna()
            if mask.any():
                try:
                    # If already timezone-aware, convert to selected timezone
                    if hasattr(df[col].dt, 'tz'):
                        df.loc[mask, col] = df.loc[mask, col].dt.tz_convert(timezone)
                    else:
                        # If naive, assume UTC and convert to selected timezone
                        df.loc[mask, col] = df.loc[mask, col].dt.tz_localize('UTC').dt.tz_convert(timezone)
                    
                    # Format to string
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    # If conversion fails, use naive formatting
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Fill any remaining NaT with empty string for display
            df[col] = df[col].fillna('')
    return df

def display_user(user, info_container):
    """
    Display user information in a formatted way, distributed across three columns.
    
    Args:
        user (dict): User information to display
        info_container: Streamlit container for the user display
    """
    with info_container:
        # Get timezone from context, default to 'America/Los_Angeles' if not set
        context = st.session_state.get('app_context', {})
        timezone = context.get('timezone', 'America/Los_Angeles')
        
        # Create three columns for better layout
        col1, col2, col3 = st.columns([1, 1, 1])
        
        # Display user data in a vertical format
        for i, (key, value) in enumerate(user.items()):
            # Convert timestamp to local time if needed
            if key in ['created_at', 'updated_at'] and value is not None:
                try:
                    # First try parsing as UTC
                    dt = pd.to_datetime(value, utc=True, errors='coerce')
                    if pd.isna(dt):
                        # If that fails, try without timezone
                        dt = pd.to_datetime(value, errors='coerce')
                    if not pd.isna(dt):
                        # Convert to selected timezone if we have a valid datetime
                        if hasattr(dt, 'tz_localize'):
                            if dt.tz is None:
                                dt = dt.tz_localize('UTC')
                            value = dt.tz_convert(timezone).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    value = str(value)  # Fallback to string representation on error
            
            # Format the display text
            display_text = f"**{key.replace('_', ' ').title()}:** {value if value is not None else 'N/A'}"
            
            # Alternate between columns for better space usage
            if i % 3 == 0:
                col1.write(display_text)
            elif i % 3 == 1:
                col2.write(display_text)
            else:
                col3.write(display_text)

def show_user_update_page():
    """
    Display the user update interface with a form to update user information.
    """
    global UI_TEXTS
    st.subheader(f"{UI_TEXTS['MANAGE']} {UI_TEXTS['USERS']}")
    with st.container(border=True):    
        # Get user ID input
        user_id = st.number_input(
            f"{UI_TEXTS['USER']} {UI_TEXTS['ID']}:",
            min_value=1,
            value=1,
            step=1,
            help=f"{UI_TEXTS['ENTER']} {UI_TEXTS['USER']} {UI_TEXTS['ID']}"
        )
        
        # Fetch current user data
        user = None
        if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['USER']} {UI_TEXTS['DATA']}"):
            with st.spinner(f"{UI_TEXTS['USER']} {UI_TEXTS['DETAILS']}..."):
                user = dbm.get_user(user_id)
                if user:
                    st.session_state.current_user = user
                else:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['USER']} {UI_TEXTS['DATA']} {UI_TEXTS['NOT_FOUND']}")
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
                st.subheader(f"{UI_TEXTS['USER']} {UI_TEXTS['DETAILS']}")
                
                # Get available languages and current language from context
                context = st.session_state.get('app_context', {})
                available_languages = context.get('languages', ['US'])
                default_language = user.get('l10n', context.get('language', 'US'))
                
                # Create form fields with current values in a single row
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    email = st.text_input(UI_TEXTS['EMAIL'], value=user.get('email', ''))
                    
                with col2:
                    # Get current state, default to 'active' if not set
                    current_state = user.get('is_active', dbm.Subscriber_State['active'])  # Default to active (1)
                    # Find the current state key from the value
                    current_state_key = next(
                        (k for k, v in dbm.Subscriber_State.items() if v == current_state),
                        'active'  # default key if not found
                    )
                    # Define allowed states and filter the options
                    allowed_states = ['active', 'pending', 'inactive']
                    state_options = [state for state in allowed_states if state in dbm.Subscriber_State]
                    # Create selectbox with filtered state options
                    selected_state = st.selectbox(
                        UI_TEXTS['SUBSCRIBER_STATE'],
                        options=state_options,
                        index=state_options.index(current_state_key) 
                        if current_state_key in state_options else 0
                    )
                    # Store the numeric value of the selected state
                    is_active = dbm.Subscriber_State[selected_state]
                with col3:
                    l10n = st.selectbox(
                        UI_TEXTS['LANGUAGE'],
                        options=available_languages,
                        index=available_languages.index(default_language) if default_language in available_languages else 0,
                        key="l10n_select"
                    )
                
                # Submit button
                if st.form_submit_button(f"{UI_TEXTS['UPDATE']} {UI_TEXTS['USER']} {UI_TEXTS['ID']}: {user_id}"):
                    update_data = {
                        'email': email if email != user.get('email') else None,
                        'is_active': is_active,
                        'l10n': l10n if l10n != user.get('l10n') else None
                    }
                    
                    # Remove None values
                    update_data = {k: v for k, v in update_data.items() if v is not None}
                    
                    if update_data:
                        if dbm.update_user(user_id, update_data):
                            st.success(f"✅ {UI_TEXTS['UPDATE']} {UI_TEXTS['USER']}: {user_id} {UI_TEXTS['SUCCEEDED']}!")
                            # Refresh the user data
                            if 'current_user' in st.session_state:
                                del st.session_state.current_user
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['UPDATE']} {UI_TEXTS['USER']}: {user_id} {UI_TEXTS['FAILED']}!")
        
def show_subscriber_page():
    global UI_TEXTS
    
    # Show admin sidebar
    show_admin_sidebar()
    context = st.session_state.get('app_context', cu.init_context())
    
    # --- manage users --- from here
    with st.container(border=True):
        st.subheader(f"{UI_TEXTS['QUERY']} {UI_TEXTS['SUBSCRIBER']}")
        df = pd.DataFrame()
        btn11, btn12, btn13, btn14 = st.columns([5,5,5,5])
        info1, info2, info3 = st.columns([18,1,1])
        with btn11:
            if st.button(f"{UI_TEXTS['ACTIVE']} {UI_TEXTS['SUBSCRIBERS']}"):
                users = dbm.get_subscribers(state="active")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"ℹ️ {len(users)} {UI_TEXTS['ACTIVE']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['RETRIEVED']}")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info(f"ℹ️ {UI_TEXTS['ACTIVE']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['NOT_FOUND']}")
        with btn12:
            if st.button(f"{UI_TEXTS['INACTIVE']} {UI_TEXTS['SUBSCRIBERS']}"):
                users = dbm.get_subscribers(state="inactive")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"ℹ️ {len(users)} {UI_TEXTS['INACTIVE']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['RETRIEVED']}")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info(f"ℹ️ {UI_TEXTS['INACTIVE']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['NOT_FOUND']}")
        with btn13:
            if st.button(f"{UI_TEXTS['PENDING']} {UI_TEXTS['SUBSCRIBERS']}"):
                users = dbm.get_subscribers(state="pending")
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"ℹ️ {len(users)} {UI_TEXTS['PENDING']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['RETRIEVED']}")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info(f"ℹ️ {UI_TEXTS['PENDING']} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['NOT_FOUND']}") 
                        
        with btn14:
            if st.button(f"{UI_TEXTS['ALL']} {UI_TEXTS['SUBSCRIBERS']}"):
                users = dbm.get_subscribers('all')
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"ℹ️ {len(users)} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['RETRIEVED']}")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info(f"ℹ️ {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['NOT_FOUND']}")
    
        col1, col2 = st.columns([5,5])
        with col1:
            email = st.text_input(f'{UI_TEXTS["EMAIL"]}:', 
                        value=st.session_state.user_email)
            if email:  # Only call strip() if email is not None
                email = email.strip()
            else:
                email = ''  # Set default empty string if email is None
        with col2:
            lang_list = dbm.get_article_languages()
            l10n = st.selectbox(f'{UI_TEXTS["LANGUAGE"]}:', 
                                lang_list,
                                index=0 if not context.get('language') else lang_list.index(context.get('language'))
                                )
        user_id = None
        # Create two columns for the query buttons
        col_query1, col_query2 = st.columns(2)
        
        with col_query1:
            if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['BY_EMAIL']}", use_container_width=True):
                user = dbm.get_subscriber(email)
                if user is not None:
                    user_id = user.get('id')
                    # Create a vertical display of user data
                    st.write(f"### {UI_TEXTS['USER']} {UI_TEXTS['DETAILS']}")   
                    display_user(user, info1)           
                else:            
                    st.warning(f"️⚠️  {fu.get_function_name()}: Email '{email}' not found")
        
        with col_query2:
            if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['BY_LANGUAGE']}", use_container_width=True):
                users = dbm.get_subscribers(lang=l10n)
                if users:
                    df = pd.DataFrame(users, columns=users[0].keys())
                    df = format_timestamps(df)
                    with info1:
                        st.info(f"ℹ️ {len(users)} {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['RETRIEVED']}")
                        st.dataframe(df)
                else:
                    with info1:
                        st.info(f"ℹ️ {UI_TEXTS['SUBSCRIBERS']} {UI_TEXTS['NOT_FOUND']}")
             
        # --- manage a specific subscriber --- from here
        st.subheader(f"{UI_TEXTS['MANAGE']} {UI_TEXTS['SUBSCRIBER']}")
        btn21, btn22 = st.columns([5,5])
    
        with btn21:
            if st.button(f"{UI_TEXTS['SUBSCRIBE']}: {email}"):
                user_data = {
                    'email': email,
                    'is_active': dbm.Subscriber_State['active'],
                    'token': 'token',
                    'l10n': l10n
                }
                if dbm.add_or_update_subscriber(user_data):
                    cu.update_context({'language': l10n})
                    st.info(f"ℹ️ {UI_TEXTS['SUBSCRIBE']}: {email} {UI_TEXTS['SUCCEEDED']}")
                else:
                    st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['SUBSCRIBE']}: {email} {UI_TEXTS['FAILED']}")
    
        with btn22:
            if st.button(f"{UI_TEXTS['UNSUBSCRIBE']}: {email}"):
                if dbm.remove_subscriber(email):
                    st.info(f"ℹ️ {UI_TEXTS['UNSUBSCRIBE']}: {email} {UI_TEXTS['SUCCEEDED']}")
                else:
                    st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['UNSUBSCRIBE']}: {email} {UI_TEXTS['FAILED']}")
    
        # --- manage a specific user --- from here
        with st.expander(f"{UI_TEXTS['DANGER_ZONE']}", expanded=False):
            st.warning(f"⚠️ {UI_TEXTS['CANNOT_BE_UNDONE']}")
            col221, col222 = st.columns([5,5])
            with col221:
                if st.button(f"{UI_TEXTS['DELETE']} {UI_TEXTS['EMAIL']}: {email}"):
                    if not email:
                        st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['EMAIL']} {UI_TEXTS['REQUIRED']}")
                        return
                    if dbm.delete_subscriber(email):
                        st.info(f"ℹ️ {UI_TEXTS['DELETE']} {UI_TEXTS['EMAIL']}: {email} {UI_TEXTS['SUCCEEDED']}")
                    else:
                        st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['DELETE']} {UI_TEXTS['EMAIL']}: {email} {UI_TEXTS['FAILED']}")
            with col222:
                if st.button(f"{UI_TEXTS['DELETE']} {UI_TEXTS['USER']} {UI_TEXTS['ID']}: {user_id}"):
                    if not user_id:
                        st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['USER']} {UI_TEXTS['ID']} {UI_TEXTS['REQUIRED']}")
                        return
                    if dbm.delete_user(user_id):
                        st.info(f"ℹ️ {UI_TEXTS['DELETE']} {UI_TEXTS['USER']} {UI_TEXTS['ID']}: {user_id} {UI_TEXTS['SUCCEEDED']}")
                    else:
                        st.warning(f"️⚠️ {fu.get_function_name()}: {UI_TEXTS['DELETE']} {UI_TEXTS['USER']} {UI_TEXTS['ID']}: {user_id} {UI_TEXTS['FAILED']}")

def main():
    global UI_TEXTS
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.switch_page("subs_ui.py")
    else:
        st.header(f"{UI_TEXTS['USER']} {UI_TEXTS['MANAGEMENT']}")
        show_subscriber_page()
        show_user_update_page()
        
# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]

if __name__ == "__main__":
    main()
