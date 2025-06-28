"""
Settings Page

This module provides the settings page for the admin interface.
"""
import streamlit as st
from admin_ui import init_session_state, show_admin_sidebar
from context_utils import init_context, update_context
import db_utils as dbm
import os

# Helper function to get full file path with extension
def get_file_path():
    """Generate full file path with correct extension based on selected file type."""
    context = st.session_state.get('app_context', {})
    if not context.get('file_name') or not context.get('file_type'):
        return "No file path configured"
    extension = context.get('file_type', '').lower()
    dir_path = context.get('dir_path', '')
    return f"{os.path.join(dir_path, context['file_name'])}.{extension}"
    
# Helper function to handle export operations
def handle_export(export_func, resource_name):
    """Handle export operations with proper error handling and user feedback."""
    try:
        file_path = get_file_path()
        if not file_path:
            st.error("Please provide both file name and directory path")
            return
                
        os.makedirs(context.get('fss', {}).get('dir_path'), exist_ok=True)
        format_type = context.get('fss', {}).get('file_type').lower()
            
        if export_func(file_path, format_type):
            st.success(f"Successfully exported {resource_name} to {file_path}")
        else:
            st.error(f"Failed to export {resource_name}. Please check the logs for details.")
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    
# Helper function to handle import operations
def handle_import(import_func, resource_name):
    """Handle import operations with proper error handling and user feedback."""
    try:
        file_path = get_file_path()
        if not file_path or not os.path.exists(file_path):
            st.error(f"File not found: {file_path or 'No file specified'}")
            return
                
        format_type = context.get('fss', {}).get('file_type').lower()
        success, error, skipped = import_func(file_path, format_type)
            
        st.info(
            f"{resource_name} import completed. "
            f"Success: {success}, Errors: {error}, Skipped: {skipped}"
            )
            
    except Exception as e:
        st.error(f"An error occurred during import: {str(e)}")

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")

def show_front_end():
    st.subheader("Front-end Settings")
   
    with st.form("front_end_form"):
        # Add your settings form fields here
        
        # 使用 context 初始化表單
        timezone = st.selectbox(
            "Select Timezone",
            ["UTC", "America/Los_Angeles", "Asia/Taipei"],
            index=0 if not context.get('timezone') else 
                ["UTC", "America/Los_Angeles", "Asia/Taipei"].index(context.get('timezone', 'UTC'))
        )
        context['timezone'] = timezone
        
        lang_list = dbm.get_article_languages()
        language = st.selectbox(
            "Select Language",
            lang_list,
            index=0 if not context.get('language') else lang_list.index(context.get('language'))
        )
        context['language'] = language
        email_notifications = st.checkbox("Enable Email Notifications", value=True)
        default_email = st.text_input("Default Email", 
                    value=context.get('default_email'))
        dark_mode = st.checkbox("Enable Dark Mode", value=False)
        context['default_email'] = default_email
        context['email_notifications'] = email_notifications
        context['dark_mode'] = dark_mode
        
        if st.form_submit_button("Save Front-end Settings"):
            update_context(context)
            st.success("Front-end Settings saved successfully!")

def show_back_end():
    st.subheader("Back-end Settings")
    # 獲取當前 context
    context = st.session_state.get('app_context', init_context())
    
    # File system settings section
    with st.form("Back-end Form"):
        # Directory path input
        context['dir_path'] = st.text_input(
            "Directory Path",
            value=context.get('fss', {}).get('dir_path', ''),
            help="Enter the directory path where files will be saved/loaded"
        )
        
        # File settings in columns for better layout
        col11, col12 = st.columns([3, 2])
        with col11:
            # File name input
            context['file_name'] = st.text_input(
                "File Name",
                value=context.get('fss', {}).get('file_name', ''),
                help="Enter the base file name (without extension)"
            )
        with col12:
            # File type selection
            context['file_type'] = st.selectbox(
                "File Type",
                ["JSON", "CSV"],
                index=0 if not context.get('fss', {}).get('file_type') else 
                    ["JSON", "CSV"].index(context.get('fss', {}).get('file_type', 'JSON')),
                help="Select the file format for import/export"
            )
        if st.form_submit_button("Save Back-end Settings"):
            update_context(context)
            file_path = get_file_path()
            st.success(f"{file_path} saved successfully!")
    
    col21, col22 = st.columns([1, 1])
    with col21:
        file_path = get_file_path()
        st.markdown("File Destination:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📤 Export Users", type="primary", help="Export user data to selected file format"):
            handle_export(dbm.export_users_to_file, "users")
    with col22:
        file_path = get_file_path()
        st.markdown("File Source:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📥 Import Users", type="secondary", help="Import user data from selected file"):
            handle_import(dbm.import_users_from_file, "Users")
    
    col31, col32 = st.columns([1, 1])
    with col31:
        file_path = get_file_path()
        st.markdown("File Destination:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📤 Export Articles", type="primary", help="Export article data to selected file format"):
            handle_export(dbm.export_articles_to_file, "articles")
    with col32:
        file_path = get_file_path()
        st.markdown("File Source:")
        st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
        if st.button("📥 Import Articles", type="secondary", help="Import article data from selected file"):
            handle_import(dbm.import_articles_from_file, "Articles")
    
# Show the page if authenticated
# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
st.title("Settings")
# 獲取當前 context
context = st.session_state.get('app_context', init_context())
show_front_end()
st.markdown("---")
show_back_end()

