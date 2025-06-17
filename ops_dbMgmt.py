"""
Database Management Tool

This module provides database management features including:
- Table structure modifications
- Database maintenance
- Data migration
"""

import sqlite3
import streamlit as st
import db_utils as dbm
import hashlib
import secrets
from admin_ui import show_login_page, show_admin_sidebar, show_main_content, init_session_state

def init_admin_features():
    """Initialize admin features by adding necessary columns to user table"""
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if password_hash column exists
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add password_hash column if it doesn't exist
            if 'password_hash' not in columns:
                cursor.execute("""
                    ALTER TABLE user ADD COLUMN password_hash TEXT
                """)
            
            # Add salt column if it doesn't exist
            if 'salt' not in columns:
                cursor.execute("""
                    ALTER TABLE user ADD COLUMN salt TEXT
                """)
            
            # Add is_admin column if it doesn't exist
            if 'is_admin' not in columns:
                cursor.execute("""
                    ALTER TABLE user ADD COLUMN is_admin INTEGER DEFAULT 0
                """)
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        st.error(f"Error initializing admin features: {e}")
        return False

def hash_password(password, salt=None):
    """Hash password with salt using PBKDF2"""
    if salt is None:
        salt = secrets.token_hex(16)  # Generate random salt
    
    # Use SHA-256 for password hashing
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),  # Convert password to bytes
        salt.encode('utf-8'),      # Use salt
        100000                     # Number of iterations
    ).hex()
    
    return password_hash, salt

def create_admin_user(email, password):
    """Create a new admin user"""
    try:
        # Check if user already exists
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user to be admin
                user_id = existing_user[0]
                password_hash, salt = hash_password(password)
                cursor.execute("""
                    UPDATE user 
                    SET password_hash = ?, salt = ?, is_admin = 1, is_active = 1
                    WHERE id = ?
                """, (password_hash, salt, user_id))
                conn.commit()
                return True, "Existing user updated to admin"
            else:
                # Create new admin user
                password_hash, salt = hash_password(password)
                cursor.execute("""
                    INSERT INTO user (email, password_hash, salt, is_admin, is_active)
                    VALUES (?, ?, ?, 1, 1)
                """, (email, password_hash, salt))
                conn.commit()
                return True, "Admin user created successfully"
                
    except sqlite3.Error as e:
        return False, f"Error creating admin user: {e}"

def verify_admin(email, password):
    """Verify admin credentials"""
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, password_hash, salt, is_admin 
                FROM user 
                WHERE email = ? AND is_admin = 1
            """, (email,))
            
            result = cursor.fetchone()
            if result is None:
                return False
                
            user_id, stored_hash, salt, is_admin = result
            if not is_admin:
                return False
                
            input_hash, _ = hash_password(password, salt)
            
            if input_hash == stored_hash:
                # Update last login time
                cursor.execute("""
                    UPDATE user 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
                return True
                
            return False
            
    except sqlite3.Error:
        return False

def add_column_if_not_exists(table_name, column_name, column_definition):
    """
    Add a column to the specified table if it doesn't exist
    
    Args:
        table_name (str): Name of the table
        column_name (str): Name of the column to add
        column_definition (str): Column definition (e.g., "TEXT NOT NULL DEFAULT 'US'")
        
    Returns:
        bool: Returns True if successfully added or column already exists, False otherwise
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if column_name not in columns:
                # Column doesn't exist, add it
                alter_table_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                cursor.execute(alter_table_sql)
                conn.commit()
                return True
            return True
    except sqlite3.Error as e:
        st.error(f"Error adding column: {e}")
        return False

def remove_column_if_exists(table_name, column_name):
    """
    Remove a column from the specified table if it exists
    
    Args:
        table_name (str): Name of the table
        column_name (str): Name of the column to remove
        
    Returns:
        bool: Returns True if successfully removed or column doesn't exist, False otherwise
    """
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # SQLite doesn't support DROP COLUMN directly, so we need to create a new table
            # without the column and copy the data over
            
            # Get the table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Check if column exists
            column_names = [col[1] for col in columns]
            if column_name not in column_names:
                return True  # Column doesn't exist, nothing to do
                
            # Create a new table without the column
            temp_table = f"{table_name}_temp"
            
            # Generate the CREATE TABLE statement for the new table
            create_table_sql = f"CREATE TABLE {temp_table} ("
            for col in columns:
                if col[1] == column_name:
                    continue  # Skip the column we want to remove
                create_table_sql += f"{col[1]} {col[2]},"
            create_table_sql = create_table_sql.rstrip(",") + ")"
            
            # Create the new table
            cursor.execute(create_table_sql)
            
            # Copy data from old table to new table
            insert_columns = ", ".join([col[1] for col in columns if col[1] != column_name])
            cursor.execute(f"INSERT INTO {temp_table} SELECT {insert_columns} FROM {table_name}")
            
            # Drop the old table
            cursor.execute(f"DROP TABLE {table_name}")
            
            # Rename the new table to the original name
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
            
            conn.commit()
            return True
    except sqlite3.Error as e:
        st.error(f"Error removing column: {e}")
        return False

def init_db_management():
    """Initialize database management page"""
    st.header("Table Structure Management")
    
    # Get available tables from the database
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                st.warning("No tables found in the database")
                return None
                
            # Select table to manage
            table = st.selectbox("Select Table", tables)
            
            st.subheader(f"Manage Table: {table}")
            
            # Display current table structure
            if st.button(f"Show {table} Table Structure"):
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    if not columns:
                        st.warning(f"No columns found in table: {table}")
                    else:
                        st.write("### Table Structure")
                        column_data = []
                        for col in columns:
                            # Handle case where column info might be missing some fields
                            col_info = {
                                "Column Name": col[1] if len(col) > 1 else "N/A",
                                "Data Type": col[2] if len(col) > 2 else "N/A",
                                "Allow NULL": "No" if (len(col) > 3 and col[3]) else "Yes",
                                "Default": str(col[4]) if len(col) > 4 and col[4] is not None else "None",
                                "Primary Key": "Yes" if (len(col) > 5 and col[5]) else "No"
                            }
                            column_data.append(col_info)
                        
                        st.table(column_data)
                        
                except sqlite3.Error as e:
                    st.error(f"Error fetching table structure: {e}")
                    return None
                    
            return table
            
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="Database Management",
        page_icon="🛠️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Initialize admin features (adds necessary columns to user table)
    if not init_admin_features():
        st.error("Failed to initialize admin features")
        st.stop()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        show_login_page()
        st.stop()
    
    # Show admin interface
    show_admin_sidebar()
    show_main_content()
    
    # Footer
    st.markdown(
        """
        ---
        ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
        """
    )
    
