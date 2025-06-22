"""
Script to create the first admin user in the database.
"""
import os
import sqlite3
from dotenv import load_dotenv
from db_utils import db_path, init_db
import auth_utils as auth

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    email = os.getenv('DB_ADMIN')
    password = os.getenv('DB_ADMIN_PW')
    
    if not email or not password:
        print("Error: DB_ADMIN and DB_ADMIN_PW must be set in .env file")
        exit(1)
    
    # First, try to delete existing user if any to avoid conflicts
    try:
        if os.path.exists(db_path):
            init_db()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            print(f"Removed existing user: {email}")
    except Exception as e:
        print(f"Warning: {e}")
    
    # Now create the admin user
    if auth.create_admin_user(email, password):
        print(f"\nSuccessfully created admin user:")
        print(f"Email: {email}")
        print(f"Password: {password}")
    else:
        print("Failed to create admin user.")
