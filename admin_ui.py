"""
Admin UI Components

This module provides UI components for the admin interface.
"""
import streamlit as st
import sqlite3
import db_utils as dbm
from ops_dbMgmt import (
    create_admin_user,
    verify_admin,
    init_db_management
)

def show_login_page():
    """Display the login page"""
    st.title("Database Management")
    st.markdown("---")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("<h2 style='text-align: center;'>Admin Login</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if verify_admin(email, password):
                        st.session_state.authenticated = True
                        st.session_state.user_email = email  # Store the logged-in user's email
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
    return False

def show_admin_sidebar():
    """Display the admin sidebar with user management controls"""
    with st.sidebar:
        st.header("Admin")
        st.divider()
        st.header("User Management")
        
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
                        st.error("Please enter a valid email address")
                    elif not new_password:
                        st.error("Please enter a password")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    else:
                        success, message = create_admin_user(email, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            # Display current admin users
            st.subheader("Current Admin Users")
            try:
                with dbm.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT email, created_at, updated_at 
                        FROM user 
                        WHERE is_admin = 1
                        ORDER BY email
                    """)
                    admins = cursor.fetchall()
                    
                    if admins:
                        admin_list = [{"Email": email, "Created": created, "Last Updated": updated}
                                    for email, created, updated in admins]
                        st.table(admin_list)
                    else:
                        st.info("No admin users found")
                        
            except sqlite3.Error as e:
                st.error(f"Error fetching admin users: {e}")
                
        # Add current user info and logout button at the bottom of the sidebar
        st.divider()
        
        # Display current user email if available
        if 'user_email' in st.session_state:
            st.markdown(
                f"""
                <div style="margin: 10px 0; padding: 10px; 
                            background-color: #2E7D32;  /* Darker green for better contrast */
                            color: white;
                            border-radius: 5px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            font-size: 0.9em;">
                    <span style="font-weight: bold; display: block; margin-bottom: 4px;">Logged in as:</span>
                    {st.session_state.user_email}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        if st.button("Logout", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            if 'user_email' in st.session_state:
                del st.session_state.user_email
            st.rerun()

def show_main_content():
    """Display the main content area"""
    st.title("Database Management")
    try:
        table = init_db_management()
        if not table:
            st.error("Failed to initialize database management")
            st.rerun()
            
        # Rest of your database management UI here
        st.subheader(f"Add Column to {table}")
        with st.form("add_column_form"):
            col1, col2 = st.columns(2)
            with col1:
                column_type = st.selectbox(
                    "Data Type",
                    ["TEXT", "INTEGER", "REAL", "BLOB", "TIMESTAMP", "PASSWORD"],
                    key="column_type"
                )
            with col2:
                default_value = st.text_input("Default Value (Optional)", key="default_value")
                not_null = st.checkbox("NOT NULL Constraint", key="not_null")
            
            new_column = st.text_input("New Column Name", key="new_column")
            if st.form_submit_button("Add Column"):
                if not new_column:
                    st.warning("Please enter a column name")
                    st.rerun()
                else:
                    # Build column definition
                    column_definition = "TEXT" if column_type == "PASSWORD" else column_type
                    if not_null:
                        column_definition += " NOT NULL"
                    if default_value:
                        if column_type in ["TEXT", "TIMESTAMP", "PASSWORD"]:
                            default_value = f"'{default_value}'"
                        column_definition += f" DEFAULT {default_value}"
            
                if add_column_if_not_exists(table, new_column, column_definition):
                    st.success(f"Successfully added column: {new_column}")
                else:
                    st.warning("Failed to add column: {new_column}")
    except Exception as err:
        st.error(f"add column: Caught '{err}'. class is {type(err)}")
    
    try:
        # Remove column functionality
        st.markdown(
        """
        ---
        """
        )
        st.subheader(f"Remove Column from {table}")
        old_column = st.text_input("Column Name", key="remove_column_name")
        if st.button("Remove Column"):
            if not old_column:
                st.warning("Please enter a column name")
                st.rerun()
            else:
                if remove_column_if_exists(table, old_column):
                    st.success(f"Successfully removed column: {old_column}")
                else:
                    st.warning(f"Failed to remove column: {old_column}")
    except Exception as err:
        st.error(f"remove column: Caught '{err}'. class is {type(err)}")
    
    try:    
        # Drop table functionality
        st.markdown(
        """
        ---
        """
        )
        st.subheader(f"Drop {table}")
        if st.button(f"Drop {table}"):
            st.warning(f"⚠️ Are you sure you want to drop {table}? This action cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Yes, Drop {table}", type="primary"):
                    dbm.drop_table(table)
                    st.success(f"Successfully dropped table: {table}")
            with col2:
                if st.button("Cancel"):
                    st.success("Cancelled")
    except Exception as err:
        st.error(f"drop table: Caught '{err}'. class is {type(err)}")

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
