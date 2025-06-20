"""
Settings Page

This module provides the settings page for the admin interface.
"""
import streamlit as st
from admin_ui import init_session_state, show_admin_sidebar
from context_utils import init_context, update_context
import db_utils as dbm

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")

def show():
    """Display the settings page"""
    st.title("Settings")
    st.header("Application Settings")
    # 獲取當前 context
    context = st.session_state.get('app_context', init_context())
    
    with st.form("settings_form"):
        # Add your settings form fields here
        st.subheader("General Settings")
        
        # 使用 context 初始化表單
        timezone = st.selectbox(
            "Select Timezone",
            ["UTC", "America/New_York", "Asia/Taipei"],
            index=0 if not context.get('timezone') else 
                ["UTC", "America/New_York", "Asia/Taipei"].index(context.get('timezone', 'UTC'))
        )
        context['timezone'] = timezone
        
        st.markdown("---")
        st.subheader("User Settings")
        lang_list = dbm.get_article_languages()
        language = st.selectbox(
            "Select Language",
            lang_list,
            index=0 if not context.get('language') else lang_list.index(context.get('language'))
        )
        context['language'] = language
        email_notifications = st.checkbox("Enable Email Notifications", value=True)
        default_email = st.text_input("Default Email", 
                            value=context.get('default_email', 
                            'mkaoy2k@gmail.com'))
        context['default_email'] = default_email
        dark_mode = st.checkbox("Enable Dark Mode", value=False)
        context['email_notifications'] = email_notifications
        context['dark_mode'] = dark_mode
        
        if st.form_submit_button("Save Settings"):
            update_context(context)
            st.success("Settings saved successfully!")

# Show the page if authenticated
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
show()

    
