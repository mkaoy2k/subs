"""
Script to create the first admin user in the database.
"""
import os
import sqlite3
from dotenv import load_dotenv
import auth_utils as auth
import db_utils as dbm

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
        if os.path.exists(dbm.db_path):
            dbm.init_db()
            conn = sqlite3.connect(dbm.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {dbm.db_tables['user']} 
                WHERE email = ?
                """, (email,))
            conn.commit()
            conn.close()
            print(f"Removed existing user: {email}")
   
        # Now create the admin user
        user_id = auth.create_admin_user(email, password)
        if user_id:
            print(f"\nSuccessfully created admin user:")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"{dbm.get_user(user_id)}")
        else:
            print("Failed to create admin user.")
    except Exception as e:
        print(f"Error: {e}")
