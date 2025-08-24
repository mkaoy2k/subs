"""
Authentication Utilities

This module handles authentication-related functions to avoid circular imports.
"""
import streamlit as st
import sqlite3
import hashlib
import secrets
import db_utils as dbm
from datetime import datetime

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

def verify_admin(email, password):
    """Verify admin credentials"""
    try:
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, password_hash, salt, is_admin 
                FROM user 
                WHERE email = ? 
                AND (is_admin = {dbm.User_State['p_admin']} OR is_admin = {dbm.User_State['f_admin']})
            """, (email,))
            
            result = cursor.fetchone()
            if result is None:
                return False
                
            user_id, stored_hash, salt, is_admin = result
            if not is_admin:
                return False
                
            input_hash, _ = hash_password(password, salt)
            
            if input_hash == stored_hash:
                # Update last login time with current timestamp
                try:
                    cursor.execute(f"""
                        UPDATE user 
                        SET updated_at = datetime('now')
                        WHERE id = ?
                    """, (user_id,))
                    conn.commit()
                except sqlite3.Error as update_error:
                    st.error(f"️❌ {fu.get_function_name()}: Error updating login time: {update_error}")
                    # Continue even if update fails, as auth was successful
                return True
            
            return False
            
    except sqlite3.Error as e:
        st.error(f"️❌ {fu.get_function_name()}: Error verifying admin: {e}")
        return False

def create_admin_user(email, password):
    """Create a new admin user and return 
    user id if successful, None otherwise
    """
    try:
        # Check if user already exists
        with dbm.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM user WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            # Get current timestamp
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if existing_user:
                # Update existing user to be admin
                user_id = existing_user[0]
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    UPDATE {dbm.db_tables['user']} 
                    SET password_hash = ?, 
                        salt = ?, 
                        is_admin = {dbm.User_State['p_admin']}, 
                        is_active = {dbm.Subscriber_State['active']},
                        created_at = ?
                    WHERE id = ?
                """, (password_hash, salt, now, user_id))
                conn.commit()
                return user_id
            else:
                # Create new admin user
                password_hash, salt = hash_password(password)
                cursor.execute(f"""
                    INSERT INTO {dbm.db_tables['user']} (
                        email, 
                        password_hash, 
                        salt, 
                        is_admin, 
                        is_active,
                        created_at 
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, 
                (email, password_hash, salt, 
                 dbm.User_State['p_admin'], 
                 dbm.Subscriber_State['active'], 
                 now)
                )
                user_id = cursor.lastrowid
                conn.commit()
                return user_id
                
    except sqlite3.Error as e:
        return None