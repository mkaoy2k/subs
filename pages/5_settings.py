"""
Settings Page

This module provides the settings page for the admin interface.
"""
import streamlit as st
import subs_ui as subs
import context_utils as cu
import db_utils as dbm

def show_front_end():
    st.subheader("Front-end Settings")
    # initialize App context
    context = st.session_state.get('app_context', cu.init_context())
    with st.form("front_end_form"):
        # Add your settings form fields here
        
        col1, col2 = st.columns(2)
        # 使用 context 初始化表單
        with col1:
            timezone = st.selectbox(
                "Select Timezone",
                ["UTC", "America/Los_Angeles", "Asia/Taipei"],
                index=0 if not context.get('timezone') else 
                    ["UTC", "America/Los_Angeles", "Asia/Taipei"].index(context.get('timezone', 'UTC'))
            )
            email_user = st.text_input("Default Email", 
                        value=st.session_state.user_email)
            context['timezone'] = timezone
            context['email_user'] = email_user
        
        with col2:
            lang_list = dbm.get_article_languages()
            if not lang_list:
                lang_list = ["US", "繁中"]
            language = st.selectbox(
                "Select Language",
                lang_list,
                index=0 if not context.get('language') else lang_list.index(context.get('language'))
            )
            admin_email = st.text_input("Admin Email", 
                        value=st.session_state.user_email)
            context['language'] = language
            context['admin_email'] = admin_email
        
        email_subscription = st.checkbox("Enable Email Subscription", value=True)
        dark_mode = st.checkbox("Enable Dark Mode", value=False)
        context['email_subscription'] = email_subscription
        context['dark_mode'] = dark_mode
        
        if st.form_submit_button("Save Front-end Settings"):
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
                    st.success("Front-end Settings saved successfully!")
                else:
                    st.error("Front-end Settings saved failed!")
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
                    st.success("Front-end Settings saved successfully!")
                else:
                    st.error("Front-end Settings saved failed!")

def show_back_end():
    st.subheader("Back-end Settings")
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
        if st.form_submit_button(" Save Back-end Settings"):
            # Update context with new values
            context['fss'] = {
                'dir_path': dir_path,
                'file_name': filename,
                'file_type': file_type
            }
            cu.update_context(context)
            st.success("Back-end settings saved successfully!")
    
    # Import/Export section (outside the form)
    st.subheader("Data Management")
    with st.container(border=True):
        # Export/Import buttons in columns
        col21, col22 = st.columns([1, 1])
        with col21:
            file_path = cu.get_file_path()
            st.markdown("File Destination:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"Export {dbm.db_tables['user']}", type="secondary", help="Export user data to selected file"):
                results = dbm.export_to_file(file_path, 
                                    dbm.db_tables['user'])
                if results['success']:
                    st.success(f"table {dbm.db_tables['user']} exported {results['count']} records successful in {results['file_path']}!")
                else:
                    st.error(f"table {dbm.db_tables['user']} export failed: {results['message']}")
    
        with col22:
            file_path = cu.get_file_path()
            st.markdown("File Source:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            col221, col222 = st.columns([1, 1])
            with col221:
                if st.button(f"Import {dbm.db_tables['user']}", type="secondary", help="Import user data from selected file"):
                    results = dbm.import_from_file(file_path, 
                                        dbm.db_tables['user'])
                    if results['success']:
                        st.success(f"Imported {results['imported']} users, skipped {results['skipped']} users")
                    else:
                        st.error(f"Imported {results['imported']} users, skipped {results['skipped']} users")
                    # show error messages
                    for error in results['errors']:
                        st.error(error)
            with col222:
                if st.button(f"Import subscribers", type="secondary", help="Import subscriber data from selected file"):
                    results = dbm.import_from_file(file_path, 
                                        dbm.db_tables['subscriber'])
                    if results['success']:
                        st.success(f"Imported {results['imported']} subscribers, skipped {results['skipped']} subscribers")
                    else:
                        st.error(f"Imported {results['imported']} subscribers, skipped {results['skipped']} subscribers")
                    # show error messages
                    for error in results['errors']:
                        st.error(error)

        col31, col32 = st.columns([1, 1])
        with col31:
            file_path = cu.get_file_path()
            st.markdown("File Destination:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"Export {dbm.db_tables['article']}", type="secondary", help="Export article data to selected file"):
                results = dbm.export_to_file(file_path, 
                               dbm.db_tables['article'])
                if results['success']:
                    st.success(f"table {dbm.db_tables['article']} exported {results['count']} records successful in {results['file_path']}!")
                else:
                    st.error(f"table {dbm.db_tables['article']} export failed: {results['message']}")
    
        with col32:
            file_path = cu.get_file_path()
            st.markdown("File Source:")
            st.markdown(f"<p style='font-size: 20px; font-weight: bold;'>{file_path}</p>", unsafe_allow_html=True)
            if st.button(f"Import {dbm.db_tables['article']}", type="secondary", help="Import article data from selected file"):
                results = dbm.import_from_file(file_path, 
                               dbm.db_tables['article'])
                if results['success']:
                    st.success(f"Imported {results['imported']} articles, skipped {results['skipped']} articles")
                else:
                    st.error(f"Imported {results['imported']} articles, skipped {results['skipped']} articles")
                # show error messages
                for error in results['errors']:
                    st.error(error)
    
# Initialize session state
subs.init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("subs_ui.py")
    
# admin sidebar --- from here
subs.show_admin_sidebar()

# Main content --- from here
st.title("Settings")
show_front_end()
show_back_end()

