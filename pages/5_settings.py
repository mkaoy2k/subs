"""
Settings Page

This module provides the settings page for the admin interface.
"""
import streamlit as st
from subs_ui import show_admin_sidebar
import context_utils as cu
import funcUtils as fu
import db_utils as dbm

def show_front_end():
    global UI_TEXTS
    st.subheader(f"{UI_TEXTS['FRONT_END']} {UI_TEXTS['SETTINGS']}")
    # Get current context
    context = st.session_state.get('app_context', cu.init_context())
    with st.form("front_end_form"):
        col1, col2 = st.columns(2)
        with col1:
            timezone = st.selectbox(
                f"{UI_TEXTS['SELECT']} {UI_TEXTS['TIMEZONE']}",
                ["UTC", "America/Los_Angeles", "Asia/Taipei"],
                index=0 if not context.get('timezone') else 
                    ["UTC", "America/Los_Angeles", "Asia/Taipei"].index(context.get('timezone', 'UTC'))
            )
            email_user = st.text_input(f"{UI_TEXTS['USER']} {UI_TEXTS['EMAIL']}", 
                        value=st.session_state.user_email)
            email_subscription = st.checkbox(f"{UI_TEXTS['ENABLE']} {UI_TEXTS['EMAIL']} {UI_TEXTS['SUBSCRIPTION']}", value=True)
            context['timezone'] = timezone
            context['email_user'] = email_user
            context['email_subscription'] = email_subscription
            save_clicked = st.form_submit_button(f"{UI_TEXTS['SAVE']}", type="primary")
        
        with col2:
            lang_list = dbm.get_article_languages()
            if not lang_list:
                lang_list = ["US", "繁中"]
            language = st.selectbox(
                f"{UI_TEXTS['SELECT']} {UI_TEXTS['LANGUAGE']}",
                lang_list,
                index=0 if not context.get('language') else lang_list.index(context.get('language'))
            )
            admin_email = st.text_input(f"{UI_TEXTS['ADMIN']} {UI_TEXTS['EMAIL']}", 
                        value=st.session_state.user_email)
            dark_mode = st.checkbox(f"{UI_TEXTS['ENABLE']} {UI_TEXTS['DARK_MODE']}", value=False)
            context['language'] = language
            context['admin_email'] = admin_email
            context['dark_mode'] = dark_mode
            refresh_clicked = st.form_submit_button(f"{UI_TEXTS['REFRESH']}", type="secondary")
        
        if refresh_clicked:
            cu.update_context(context)
            st.rerun()
            
        if save_clicked:
            if email_subscription:
                user_data = {
                    'email': email_user,
                    'is_active': dbm.Subscriber_State['active'],
                    'token': 'Front-end Subscription',
                    'l10n': language
                }
                if dbm.add_or_update_subscriber(user_data, 
                            update=True):
                    cu.update_context(context)
                    st.success(f"✅ {UI_TEXTS['SAVE']} {UI_TEXTS['FRONT_END']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['SUCCEEDED']}!")
                else:
                    st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['SAVE']} {UI_TEXTS['FRONT_END']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['FAILED']}!")
            else:
                user_data = {
                    'email': email_user,
                    'is_active': dbm.Subscriber_State['inactive'],
                    'token': 'Front-end Subscription',
                    'l10n': language
                }
                if dbm.add_or_update_subscriber(user_data, 
                            update=True):
                    cu.update_context(context)
                    st.success(f"✅ {UI_TEXTS['SAVE']} {UI_TEXTS['FRONT_END']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['SUCCEEDED']}!")
                else:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['SAVE']} {UI_TEXTS['FRONT_END']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['FAILED']}!")

def show_back_end():
    global UI_TEXTS
    st.subheader(f"{UI_TEXTS['BACK_END']} {UI_TEXTS['SETTINGS']}")
    # Get current context
    context = st.session_state.get('app_context', cu.init_context())
    
    # File system settings section - wrapped in a form
    with st.form("back_end_form"):
        # Directory path input
        dir_path = st.text_input(
            "Directory Path",
            value=context.get('fss', {}).get('dir_path', ''),
            help="Enter the directory path where files will be saved/loaded"
        )
        
        # File settings in columns for better layout
        col11, col12 = st.columns([3, 2])
        with col12:
            # File type selection
            file_type = st.selectbox(
                "File Type",
                ["JSON", "CSV"],
                index=0 if context.get('fss', {}).get('file_type', 'JSON') == 'JSON' else 1
            )
            
        with col11:
            # Timezone selection
            filename = st.text_input(
                "Filename",
                value=context.get('fss', {}).get('file_name', ''),
                help="Enter the filename where files will be saved/loaded"
            )
        
        # Form submission button
        if st.form_submit_button(f"{UI_TEXTS['SAVE']}", type='primary'):
            # Update context with new values
            context['fss'] = {
                'dir_path': dir_path,
                'file_name': filename,
                'file_type': file_type
            }
            cu.update_context(context)
            st.success(f"✅ {UI_TEXTS['SAVE']} {UI_TEXTS['BACK_END']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['SUCCEEDED']}!")
    
    # Import/Export section (outside the form)
    st.subheader(f"{UI_TEXTS['DATA']} {UI_TEXTS['MANAGEMENT']}")
    with st.container(border=True):
        # Export/Import buttons for users and subscribers
        col21, col22 = st.columns([1, 2])
        with col21:
            file_path = cu.get_file_path()
            st.markdown("File Destination:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"{UI_TEXTS['EXPORT']} {UI_TEXTS['USERS']}", type="primary", help="Export user data to selected file"):
                results = dbm.export_to_file(file_path, 
                                    dbm.db_tables['user'])
                if results['success']:
                    st.success(f"✅ {UI_TEXTS['TABLE']}: {dbm.db_tables['user']} {UI_TEXTS['EXPORT']} {UI_TEXTS['SUCCEEDED']}: {results['file_path']}!")
                else:
                    st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['EXPORT']} {dbm.db_tables['user']} {UI_TEXTS['FAILED']}: {results['message']}")
    
        with col22:
            file_path = cu.get_file_path()
            st.markdown("File Source:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            col221, col222 = st.columns([1, 1])
            with col221:
                if st.button(f"{UI_TEXTS['IMPORT']} {UI_TEXTS['USERS']}", type="secondary", 
                             help="Import user data from selected file"):
                    results = dbm.import_from_file(file_path, 
                                        dbm.db_tables['user'])
                    if results['success']:
                        st.success(f"✅ {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['USERS']}, skipped {results['skipped']} {UI_TEXTS['USERS']}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['USERS']}, skipped {results['skipped']} {UI_TEXTS['USERS']}")
                    # show error messages
                    for error in results['errors']:
                        st.error(f"️❌ {fu.get_function_name()}: {error}")
            with col222:
                if st.button(f"{UI_TEXTS['IMPORT']} {UI_TEXTS['SUBSCRIBERS']}", type="secondary", help="Import subscriber data from selected file"):
                    results = dbm.import_from_file(file_path, 
                                        dbm.db_tables['subscriber'])
                    if results['success']:
                        st.success(f"✅ {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['SUBSCRIBERS']}, skipped {results['skipped']} {UI_TEXTS['SUBSCRIBERS']}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['SUBSCRIBERS']}, skipped {results['skipped']} {UI_TEXTS['SUBSCRIBERS']}")
                    # show error messages
                    for error in results['errors']:
                        st.error(f"️❌ {fu.get_function_name()}: {error}")
        # Export/Import articles
        col31, col32 = st.columns([1, 2])
        with col31:
            file_path = cu.get_file_path()
            st.markdown("File Destination:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"{UI_TEXTS['EXPORT']} {UI_TEXTS['ARTICLES']}", type="secondary", help="Export article data to selected file"):
                results = dbm.export_to_file(file_path, 
                               dbm.db_tables['article'])
                if results['success']:
                    st.success(f"✅ {UI_TEXTS['EXPORT']} {dbm.db_tables['article']}: {results['count']} {UI_TEXTS['ARTICLES']} {UI_TEXTS['SUCCEEDED']}: {results['file_path']}!")
                else:
                    st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['EXPORT']} {dbm.db_tables['article']} {UI_TEXTS['FAILED']}: {results['message']}")
    
        with col32:
            file_path = cu.get_file_path()
            st.markdown("File Source:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"{UI_TEXTS['IMPORT']} {UI_TEXTS['ARTICLES']}", type="secondary", help="Import article data from selected file"):
                results = dbm.import_from_file(file_path, 
                               dbm.db_tables['article'])
                if results['success']:
                    st.success(f"✅ {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['ARTICLES']}, skipped {results['skipped']} {UI_TEXTS['ARTICLES']}")
                else:
                    st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['IMPORT']} {results['imported']} {UI_TEXTS['ARTICLES']}, skipped {results['skipped']} {UI_TEXTS['ARTICLES']}")
                # show error messages
                for error in results['errors']:
                    st.error(f"️❌ {fu.get_function_name()}: {error}")
    
# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("subs_ui.py")

# admin sidebar --- from here
show_admin_sidebar()

# Main content --- from here
st.header(f"{UI_TEXTS['SETTINGS']}")
show_front_end()
show_back_end()

