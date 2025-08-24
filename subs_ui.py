"""
Admin UI Module for Management in users, subscribers, articles, and settings.

This module provides the complete admin interface for the application.
"""
import streamlit as st
import sqlite3
import db_utils as dbm
import auth_utils as au
import context_utils as cu
import funcUtils as fu
import email_utils as eu
import pandas as pd
import os
import logging
from dotenv import load_dotenv
load_dotenv()

# Configure logger for this module
log = logging.getLogger(__name__)
# Set log level from environment variable or default to WARNING
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

# Import database operations
from ops_dbMgmt import init_db_management, init_admin_features, get_table_structure, drop_table

def show_login_page():
    """Display the login page with email and password fields.
    
    This function shows a login form with email and password fields,
    and includes a 'Forgot Password' option that allows users to
    reset their password if they've forgotten it.
    
    The function handles the following:
    - User authentication
    - Input validation
    - Password reset flow initiation
    - Error messaging
    
    Returns:
        None: Renders the login UI components directly
    """
    # Clear any existing content
    st.empty()
    
    # Initialize session state for forgot password if not exists
    if 'show_forgot_password' not in st.session_state:
        st.session_state.show_forgot_password = False
    
    # Set page title and header
    st.header(f"{os.getenv('APP_NAME', '')} {os.getenv('RELEASE', '')}")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.subheader(f"{UI_TEXTS['ADMIN']} {UI_TEXTS['LOGIN']}")
            
            # Login form
            email = st.text_input(UI_TEXTS['EMAIL'], key="login_email")
            password = st.text_input(UI_TEXTS['PASSWORD'], type="password", key="login_password")
            
            # Login and Forgot Password buttons
            col1, col2 = st.columns([2, 1])
            with col1:
                login_clicked = st.button(UI_TEXTS['LOGIN'])
            with col2:
                forgot_clicked = st.button(UI_TEXTS['FORGOT_PASSWORD'],
                                           type="secondary",
                                           icon="🔑")
            
            # Handle login
            if login_clicked:
                if not email or not password:
                    msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['EMAIL']} {UI_TEXTS['PASSWORD']} {UI_TEXTS['REQUIRED']}"
                    log.debug(msg)
                    st.error(msg)
                else:
                    if au.verify_admin(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        msg = f"✅ {UI_TEXTS['LOGIN']} {UI_TEXTS['SUCCEEDED']}!"
                        log.debug(msg)
                        st.rerun()
                    else:
                        msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['EMAIL_INVALID']}"
                        log.debug(msg)
                        st.error(msg)
            
            # Handle forgot password
            if forgot_clicked:
                st.session_state.show_forgot_password = True
            
            # Forgot password section
            if st.session_state.show_forgot_password:
                with st.expander(f"{UI_TEXTS['RESET']} {UI_TEXTS['PASSWORD']}", expanded=True):
                    reset_email = st.text_input(f"{UI_TEXTS['EMAIL']}:", 
                                             key="reset_email")
                    send_reset_clicked = st.button(f"{UI_TEXTS['EMAIL_SEND_RESET_LINK']}")
                    if send_reset_clicked:
                        if not reset_email or "@" not in reset_email:
                            msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['EMAIL_INVALID']}"
                            log.debug(msg)
                            st.error(msg)
                        else:
                            try:
                                # Generate a secure token
                                token = dbm.generate_secure_token()
                                
                                # Create reset link
                                base_url = os.getenv('BASE_URL', 'http://localhost:5000')
                                reset_link = f"{base_url}/reset-password?token={token}&email={reset_email}"
                                
                                # Get app name
                                app_name = os.getenv('APP_NAME', 'FamilyTreesOps')
                                
                                # Render HTML email template
                                html = f"""
                                <html>
                                    <body>
                                        <h2>Password Reset Request</h2>
                                        <p>Hello,</p>
                                        <p>You requested a password reset for your {app_name} account.</p>
                                        <p>Please click the button below to reset your password:</p>
                                        <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Reset Password</a></p>
                                        <p>Or copy and paste this link into your browser:<br>{reset_link}</p>
                                        <p>This link will expire in 1 hour.</p>
                                        <p>If you didn't request this, please ignore this email.</p>
                                        <p>Thanks,<br>The {app_name} Team</p>
                                    </body>
                                </html>
                                """
                                
                                # Plain text version
                                text = f"""Hello,

You requested a password reset for your {app_name} account. 
Please click the following link to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email or contact support if you have any concerns.

Thanks,
The {app_name} Team
"""
                                
                                # Initialize EmailPublisher and send email
                                try:
                                    publisher = eu.EmailPublisher(
                                        email_sender=os.getenv('MAIL_USERNAME', ''),
                                        email_password=os.getenv('MAIL_PASSWORD', '')
                                    )
                                    
                                    if publisher.publish_email(
                                        subject=f"{app_name} - Password Reset Request",
                                        text=text,
                                        html=html,
                                        recipients=[reset_email]
                                    ):
                                        # Store the reset token in the database
                                        if dbm.store_password_reset_token(reset_email, token):
                                            st.success(f"✅ Password reset link sent to {reset_email}")
                                            st.session_state.show_forgot_password = False
                                        else:
                                            st.error(f"️❌ {fu.get_function_name()}: Failed to process your request. Please try again later.")
                                    else:
                                        st.error(f"️❌ {fu.get_function_name()}: Failed to send password reset email. Please try again later.")
                                except Exception as e:
                                    st.error(f"️❌ {fu.get_function_name()}: An error occurred while sending the email: {str(e)}")
                            
                            except Exception as e:
                                st.error(f"️❌ {fu.get_function_name()}: An error occurred: {str(e)}")

def format_timestamp(ts):
    """Format timestamps for display"""
    if not ts:
        return "Never"
    try:
        # Try parsing as ISO format first
        from datetime import datetime
        if 'T' in str(ts):
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        else:
            # Try parsing as space-separated format
            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return str(ts)

def show_admin_sidebar():
    """Display the admin sidebar"""
    with st.sidebar:
        st.header(f"{UI_TEXTS['ADMIN']} {UI_TEXTS['SIDEBAR']}")
        
        # Show current user info
        if 'user_email' in st.session_state and st.session_state.user_email:
            st.markdown(
                f"<div style='background-color: #2e7d32; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem;'>"
                f"<p style='color: white; margin: 0; font-weight: bold; text-align: center;'>{st.session_state.user_email}</p>"
                "</div>",
                unsafe_allow_html=True
            )
        
        # Sidebar - Admin User Management --- from here
        st.subheader(f"{UI_TEXTS['ADMIN']} {UI_TEXTS['USER']} {UI_TEXTS['MANAGEMENT']}")
        with st.expander("Create/Update Admin User", expanded=False):
            with st.form("admin_user_form"):
                st.subheader("Admin User")
                email = st.text_input("Email", key="admin_email", 
                                   help="Enter the email address for the admin user")
                new_password = st.text_input("Password", type="password", key="new_password",
                                          help="Enter a password (at least 8 characters)")
                confirm_password = st.text_input("Confirm Password", type="password", 
                                               key="confirm_password")
                
                if st.form_submit_button("Save Admin User"):
                    if not email or "@" not in email:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['EMAIL_INVALID']}")
                    elif not new_password:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['PASSWORD']} {UI_TEXTS['REQUIRED']}")
                    elif new_password != confirm_password:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['PASSWORD']} {UI_TEXTS['NOT_MATCH']}")
                    elif len(new_password) < 8:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['PASSWORD']} {UI_TEXTS['AT_LEAST_8_CHARS']}")
                    else:
                        user_id = au.create_admin_user(email, new_password)
                        if user_id:
                            st.success(f"✅ {UI_TEXTS['CREATE']} {UI_TEXTS['ADMIN']} {UI_TEXTS['USER']} {UI_TEXTS['SUCCEEDED']}!")
                        else:
                            st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['CREATE']} {UI_TEXTS['ADMIN']} {UI_TEXTS['USER']} {UI_TEXTS['FAILED']}!")
            
        # Logout button at the bottom
        if st.sidebar.button(f"{UI_TEXTS['LOGOUT']}", type="primary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.rerun()

        # Display current admin users
        st.subheader(f"{UI_TEXTS['CURRENT']} {UI_TEXTS['ADMIN']} {UI_TEXTS['USER']}")
        try:
            with dbm.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                        SELECT id, email, created_at, updated_at 
                        FROM user 
                        WHERE is_admin = {dbm.User_State['p_admin']} or is_admin = {dbm.User_State['f_admin']}
                        ORDER BY email
                    """)
                admins = cursor.fetchall()
                
                if admins:
                    admin_list = []
                    for id, email, created_at, updated_at in admins:
                        admin_list.append({
                            "ID": id,
                            "Email": email, 
                            "Created": format_timestamp(created_at), 
                            "Last Updated": format_timestamp(updated_at)
                        })
                    # Convert to DataFrame to handle index properly
                    df = pd.DataFrame(admin_list)
                    st.dataframe(
                        df,
                        use_container_width=False,
                        hide_index=True  # Explicitly hide the index
                    )  
                else:
                    st.info(f"ℹ️ {fu.get_function_name()}: No admin users found")
            
        except sqlite3.Error as e:
            st.error(f"️❌ {fu.get_function_name()}: Error fetching admin users: {e}")

def show_main_content():
    """Display the main content area"""
    global UI_TEXTS
    
    st.header(f"{UI_TEXTS['HOME_HTML_H1']} {UI_TEXTS['ADMIN']} {UI_TEXTS['PAGE']}")
    
    # Show database tables
    st.subheader(f"{UI_TEXTS['DATABASE']} {UI_TEXTS['TABLE']}")
    tables = init_db_management()
    
    if not tables:
        st.info(f"ℹ️ {fu.get_function_name()}: No tables found in the database.")
        return
    col1, col2 = st.columns([1, 5])
    with col1:
        # Display tables in a select box
        selected_table = st.selectbox(f"{UI_TEXTS['SELECT']} {UI_TEXTS['TABLE']}", tables)
    with col2:
        st.write("\n")
    
    if selected_table:
        # Show table structure
        st.markdown(f"#### {UI_TEXTS['TABLE']} {selected_table} {UI_TEXTS['STRUCTURE']}")
        columns = get_table_structure(selected_table)
        
        if columns:
            # Display columns in a table
            column_data = []
            for col in columns:
                col_info = {
                    "Column Name": col[1],
                    "Data Type": col[2],
                    "Allow NULL": "No" if col[3] else "Yes",
                    "Default": col[4] or "None",
                    "Primary Key": "Yes" if col[5] else "No"
                }
                column_data.append(col_info)
            st.table(column_data)
            
            # Add column form
            st.markdown(f"#### {UI_TEXTS['TABLE']} {selected_table} {UI_TEXTS['ADD']} {UI_TEXTS['COLUMN']}")
            with st.expander("", expanded=False):
                st.markdown(f"#### {UI_TEXTS['DANGER_ZONE']}")
                st.warning(f"⚠️ {UI_TEXTS['CANNOT_BE_UNDONE']}")
                with st.form("add_column_form"):
                    new_col_name = st.text_input(f"{UI_TEXTS['COLUMN']} {UI_TEXTS['NAME']}")
                    col_type = st.selectbox(
                        "Data Type",
                        ["INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC"]
                    )
                    is_nullable = st.checkbox("Allow NULL", value=True)
                    default_value = st.text_input("Default Value", "")
                    
                    if st.form_submit_button(f"{UI_TEXTS['ADD']} {UI_TEXTS['COLUMN']}", type="primary"):
                        if new_col_name:
                            try:
                                # Build the ALTER TABLE statement
                                stmt = f"ALTER TABLE {selected_table} ADD COLUMN {new_col_name} {col_type}"
                                if not is_nullable:
                                    stmt += " NOT NULL"
                                if default_value:
                                    stmt += f" DEFAULT '{default_value}'"
                                
                                with dbm.get_db_connection() as conn:
                                    conn.execute(stmt)
                                    conn.commit()
                                msg = f"✅ {UI_TEXTS['ADD']} {UI_TEXTS['COLUMN']}: '{new_col_name}' {UI_TEXTS['SUCCEEDED']}"
                                log.debug(msg)
                                st.rerun()
                            except sqlite3.Error as e:
                                msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['ADD']} {UI_TEXTS['COLUMN']} {UI_TEXTS['FAILED']}: {e}"
                                log.debug(msg)
                                st.error(msg)
                        else:
                            msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['COLUMN']} {UI_TEXTS['NAME']} {UI_TEXTS['REQUIRED']}"
                            log.debug(msg)
                            st.error(msg)
            
            # Drop column form
            st.markdown(f"#### {UI_TEXTS['TABLE']} {selected_table} {UI_TEXTS['REMOVE']} {UI_TEXTS['COLUMN']}")
            with st.expander("", expanded=False):
                st.markdown(f"#### {UI_TEXTS['DANGER_ZONE']}")
                st.warning(f"⚠️ {UI_TEXTS['CANNOT_BE_UNDONE']}")
                if len(columns) > 1:  # Don't allow dropping the last column
                    with st.form("remove_column_form"):
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            col_to_remove = st.selectbox(
                                f"{UI_TEXTS['SELECT']} {UI_TEXTS['COLUMN']}:",
                                [col[1] for col in columns if col[1] != "id"]  # Don't allow dropping id column
                            )
                        with col2:
                            st.write("\n")
                            if st.form_submit_button(f"{UI_TEXTS['REMOVE']} {UI_TEXTS['COLUMN']}", type="primary"):
                                if remove_column_if_exists(selected_table, col_to_remove):
                                    msg = f"✅ {UI_TEXTS['REMOVE']} {UI_TEXTS['COLUMN']}: {col_to_remove} {UI_TEXTS['SUCCEEDED']}"
                                    log.debug(msg)
                                    st.rerun()
                                else:
                                    msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['REMOVE']} {UI_TEXTS['COLUMN']}: {col_to_remove} {UI_TEXTS['FAILED']}"
                                    log.debug(msg)
                                    st.error(msg)
                else:
                    msg = f"⚠️ {UI_TEXTS['CANNOT_REMOVE_LAST_COLUMN']}"
                    log.debug(msg)
                    st.warning(msg)
            
            # Drop table button
            st.markdown(f"#### {UI_TEXTS['TABLE']} {selected_table} {UI_TEXTS['DROP']} {UI_TEXTS['TABLE']}")
            with st.expander("", expanded=False):
                st.markdown(f"#### {UI_TEXTS['DANGER_ZONE']}")
                st.warning(f"⚠️ {UI_TEXTS['CANNOT_BE_UNDONE']}")
                if st.button(f"{UI_TEXTS['DROP']} {UI_TEXTS['TABLE']}: '{selected_table}'", type="primary"):
                    if drop_table(selected_table):
                        st.success(f"✅ {UI_TEXTS['DROP']} {UI_TEXTS['TABLE']}: {selected_table} {UI_TEXTS['SUCCEEDED']}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['DROP']} {UI_TEXTS['TABLE']}: {selected_table} {UI_TEXTS['FAILED']}")

# Main application
def main():
    """Main application entry point"""
    # Set page config
    st.set_page_config(
        page_title="Subs_UI " + os.getenv("RELEASE", ""),
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize admin features (adds necessary columns to user table)
    if not init_admin_features():
        st.error(f"️❌ {fu.get_function_name()}: Failed to initialize admin features")
        st.stop()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
    else:
        if not st.session_state.get('authenticated', False):
            show_login_page()
        else:
            show_admin_sidebar()
            # Main content
            show_main_content()

# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]
 
if __name__ == "__main__":
    main()