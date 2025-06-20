"""
Script to create an admin user in the database.
"""
import sqlite3
import hashlib
import os
import secrets
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

def create_admin_user(email, password):
    """Create or update an admin user in the database."""
    # Hash the password with a new salt
    password_hash, salt = hash_password(password)
    
    # Connect to the database
    db_path = os.path.join('data', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if user already exists
        cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        current_time = datetime.now().isoformat()
        
        if user:
            # Update existing user
            cursor.execute("""
                UPDATE user 
                SET is_admin = 1, 
                    password_hash = ?, 
                    salt = ?,
                    updated_at = ?,
                    is_active = 1
                WHERE email = ?
            """, (password_hash, salt, current_time, email))
            print(f"Updated admin user: {email}")
        else:
            # Create new admin user
            cursor.execute("""
                INSERT INTO user 
                (email, is_admin, password_hash, salt, created_at, updated_at, is_active)
                VALUES (?, 1, ?, ?, ?, ?, 1)
            """, (email, password_hash, salt, current_time, current_time))
            print(f"Created new admin user: {email}")
        
        conn.commit()
        print("Operation completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def ensure_tables_exist():
    """Ensure the user table exists with the correct schema."""
    db_path = os.path.join('data', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create user table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            is_admin INTEGER DEFAULT 0,
            password_hash TEXT,
            salt TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_active INTEGER DEFAULT 0,
            token TEXT
        )
        ''')
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    email = "mkaoy2k@me.com"
    password = "abcd1234"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Ensure tables exist
    if not ensure_tables_exist():
        print("Failed to set up database tables.")
        exit(1)
    
    # First, try to delete existing user if any to avoid conflicts
    try:
        db_path = os.path.join('data', 'users.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            print(f"Removed existing user: {email}")
    except Exception as e:
        print(f"Warning: {e}")
    
    # Now create the admin user
    if create_admin_user(email, password):
        print(f"\nSuccessfully created admin user:")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        print("Failed to create admin user.")
