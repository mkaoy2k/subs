import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv  # pip install python-dotenv
import logging

# Load the environment variables from file
load_dotenv(".env")
dbn = os.getenv("DB_NAME")
user_tbl = os.getenv("TBL_NAME")
g_logging = os.getenv("LOGGING")
logging.basicConfig(level=getattr(logging, g_logging, logging.INFO),
                    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(dbn)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        # create a table via SQL
        cmd = f"CREATE TABLE IF NOT EXISTS {user_tbl}"
        args = """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            token TEXT
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        conn.commit()

def add_subscriber(email, token):
    """Add a new subscriber or update existing one"""
    with get_db_connection() as conn:
        try:
            conn.execute(f'''
            INSERT INTO {user_tbl} (email, token, is_active, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                is_active = 1,
                token = excluded.token,
                updated_at = CURRENT_TIMESTAMP
            ''', (email, token))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_subscriber(email):
    """Unsubscribe an email"""
    with get_db_connection() as conn:
        conn.execute(f'''
        UPDATE {user_tbl} 
        SET is_active = 0, updated_at = CURRENT_TIMESTAMP 
        WHERE email = ?
        ''', (email,))
        conn.commit()
        return conn.total_changes > 0

def verify_token(email, token):
    """Verify subscription token"""
    with get_db_connection() as conn:
        cursor = conn.execute(f'''
            SELECT id FROM {user_tbl} WHERE email = ? AND token = ?''',
            (email, token)
        )
        return cursor.fetchone() is not None

# Initialize the database when this module is imported
init_db()
