"""
Database Utilities Module

This module provides functionality for interacting with SQLite databases,
including:
- Database connection management
- CRUD operations for subscriber data
- Email verification token handling
- Database initialization and configuration

Environment Variables Required:
- DB_NAME: Database file name
- TBL_USR: User table name
- TBL_ARTICLE: Article table name
- LOGGING: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)

Main Features:
- Manage subscriber emails and verification status
- Handle subscription/unsubscription processes
- Provide query interface for subscriber information
"""

import sqlite3
import os
import datetime
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Union, Optional, Tuple
import email_utils as eu
from pathlib import Path
from dotenv import load_dotenv  # pip install python-dotenv
import logging

# Load the environment variables from file
load_dotenv(".env")

# Configure logger for this module
log = logging.getLogger(__name__)
# Set log level from environment variable or default to WARNING
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

dbn = os.getenv("DB_NAME", "data/users.db")
db_path = os.path.join(os.path.dirname(__file__), dbn)
db_tables = {
    "user": os.getenv("TBL_USR", "user"),
    "article": os.getenv("TBL_ARTICLE", "article"),
    "subscriber": "subscriber"  # not a `subscriber` table, merged into user table
    }
Subscriber_State = {
    'active': 1, 
    'pending': 0,
    'inactive': -1,
    'in_contact': -2,
    'all': 9    # not used as a state but for query all-state subscribers
    }
Article_State = {
    'action_taken': 2,    # articles from contact form
    'approved': 1,        # approved articles
    'pending': 0,         # pending for review to approve or reject
    'rejected': -1,       # rejected articles
    'ignored': -2,
    'all': 9    # not used as a state but for query all-state articles
    }
# Values for Article categories
Article_Categories = {
    "news": "News", 
    "story": "Story", 
    "events": "Events", 
    "faq": "FAQ", 
    "about": "About",
    "contact": "Contact",
    "feedback": "Feedback",
    "all": "all"    # not used as a category but for query all-category articles
    }

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(dbn)
    conn.row_factory = sqlite3.Row
    return conn

def add_user_id_column():
    """Add user_id column to article table if it doesn't exist"""
    with get_db_connection() as conn:
        # Check if user_id column exists
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({db_tables['article']})")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            try:
                # Add user_id column
                conn.execute(f"ALTER TABLE {db_tables['article']} ADD COLUMN user_id INTEGER")
                log.info("Added user_id column to article table")
                return True
            except sqlite3.Error as e:
                log.error(f"Error adding user_id column: {e}")
                return False
    return False

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        # Enable foreign keys and set datetime format
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        
        # Create user table with explicit timestamp format
        cmd = f"CREATE TABLE IF NOT EXISTS {db_tables['user']}"
        args = """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 0,
            l10n TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            token TEXT,
            is_admin INTEGER DEFAULT 0,
            password_hash TEXT,
            salt TEXT
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        
        # Create article table with explicit timestamp format
        cmd = f"CREATE TABLE IF NOT EXISTS {db_tables['article']}"
        args = f""" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT {Article_Categories['news']},
            author TEXT,
            source TEXT,
            src_url TEXT,
            image_url TEXT,
            l10n TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            user_id INTEGER DEFAULT 0,
            is_censored INTEGER DEFAULT 0
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        
        # Create triggers to automatically update the updated_at timestamp
        tables_with_updated_at = [
            db_tables['user'],
            db_tables['article']
        ]
        
        for table_name in tables_with_updated_at:
            # Drop existing trigger if it exists
            drop_trigger_sql = f"""
            DROP TRIGGER IF EXISTS update_{table_name}_timestamp;
            """
            try:
                conn.execute(drop_trigger_sql)
            except sqlite3.OperationalError as e:
                log.warning(f"Failed to drop trigger for {table_name}: {str(e)}")
            
            # Create the new trigger
            create_trigger_sql = f"""
            CREATE TRIGGER IF NOT EXISTS update_{table_name}_timestamp
            AFTER UPDATE ON {table_name}
            FOR EACH ROW
            BEGIN
                UPDATE {table_name}
                SET updated_at = datetime('now')
                WHERE id = NEW.id;
            END;
            """
            try:
                conn.execute(create_trigger_sql)
                log.info(f"Created/Updated trigger for table: {table_name}")
            except sqlite3.OperationalError as e:
                log.error(f"Failed to create trigger for {table_name}: {str(e)}")
                raise
        
        conn.commit()

def add_or_update_subscriber(user_data: Dict[str, Any], 
    update: bool = True
) -> int:
    """
    Add a new subscriber with is_active status 
    or update existing one with is_active status
    
    Args:
        user_data (Dict[str, Any]): A dictionary containing user data
        update (bool): Whether to update an existing subscriber (default: True)
    
    Returns:
        int: The ID of the added or updated subscriber
        
    Raises:
        sqlite3.IntegrityError: If a subscriber with the email already exists and update=False
    Example:
        >>> add_or_update_subscriber({
            'email': 'test@example.com',
            'is_active': Subscriber_State['active'],
            'token': 'test_token',
            'l10n': 'en'
        }, update=False)
    """
    
    with get_db_connection() as conn:
        # Validate required fields
        required_fields = ['email', 'is_active', 'token', 'l10n']
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        email = user_data.get('email')
        is_active = user_data.get('is_active')
        token = user_data.get('token')
        lang = user_data.get('l10n')
        try:
            with get_db_connection() as conn:
                # First check if user exists
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT id FROM {db_tables['user']} WHERE email = ?",
                    (email,)
                )
                existing_user = cursor.fetchone()
            
                if existing_user and not update:
                    raise sqlite3.IntegrityError(f"Subscriber with email {email} already exists")
                
                if lang:
                    conn.execute(f'''
                    INSERT INTO {db_tables['user']} (
                        email, is_active, token, l10n, 
                        created_at)
                    VALUES (
                        ?, ?, ?, ?, 
                        CURRENT_TIMESTAMP
                        )
                    ON CONFLICT(email) DO UPDATE SET
                        is_active = excluded.is_active,
                        token = excluded.token,
                        l10n = excluded.l10n,
                        updated_at = CURRENT_TIMESTAMP
                    ''', (email, is_active, token, lang))
                else:
                    conn.execute(f'''
                    INSERT INTO {db_tables['user']} (
                        email, is_active, token,
                        created_at)
                    VALUES (
                        ?, ?, ?, 
                        CURRENT_TIMESTAMP)
                    ON CONFLICT(email) DO UPDATE SET
                        is_active = excluded.is_active,
                        token = excluded.token,
                        updated_at = CURRENT_TIMESTAMP
                    ''', (email, is_active, token))
                
                conn.commit()
                return True
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                error_msg = f"Subscriber with email {email} already exists"
                logging.error(f"{error_msg}: {str(e)}")
                raise sqlite3.IntegrityError(error_msg) from e
            raise  # Re-raise other integrity errors
        except Exception as e:
            conn.rollback()
            error_msg = f"Failed to add or update subscriber with email {email}"
            logging.error(f"{error_msg}: {str(e)}")
            raise Exception(error_msg) from e

def remove_subscriber(email):
    """
    Unsubscribe an email address
    
    Args:
        email (str): The email address to unsubscribe
        
    Returns:
        bool: Returns True if the record was successfully updated, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Use 'inactive' state from Subscriber_State dictionary
            inactive_state = Subscriber_State['inactive']
            
            cursor.execute(f'''
            UPDATE {db_tables['user']} 
            SET is_active = ?, 
                updated_at = CURRENT_TIMESTAMP,
                token = NULL
            WHERE email = ?
            ''', (inactive_state, email))
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"Successfully unsubscribed {email}")
                return True
            else:
                log.warning(f"No user found with email {email} to unsubscribe")
                return False
    except Exception as e:
        log.error(f"Error unsubscribing {email}: {str(e)}", exc_info=True)
        return False

def verify_token(email, token):
    """Verify subscription token"""
    with get_db_connection() as conn:
        cursor = conn.execute(f'''
            SELECT id FROM {db_tables['user']} 
            WHERE email = ? AND token = ? ''',
            (email, token)
        )
        result = cursor.fetchone()
        return result is not None

def get_subscribers(state='active', lang=None):
    """
    Fetch subscribers from the `user` table based on their 
    subscription status and language
    
    Args:
        state (str): Filter subscribers by state. 
            see Subscriber_State dictionary for valid values
        lang (str): Filter subscribers by language. 
            see L10N.json file for valid keys
            
    Returns:
        list: A list of dictionaries containing subscriber information.
              Each dictionary has keys: 
              id, email, token, is_active, created_at, updated_at
    """
    # Validate status parameter
    valid_states = [k for k in Subscriber_State.keys() if k != 'all'] + ['all']
    if state not in valid_states:
        raise ValueError(f"state must be one of: {', '.join(valid_states)}")
    
    with get_db_connection() as conn:
        
        # Build the query based on status
        if state == 'all':
            cursor = conn.execute(f"""
            SELECT * FROM {db_tables['user']} 
            ORDER BY id ASC
        """)
        else:
            if lang:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['user']} 
                WHERE is_active = ? AND l10n = ?
                ORDER BY id ASC
            """, (Subscriber_State[state], lang))
            else:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['user']} 
                WHERE is_active = ?
                ORDER BY id ASC
            """, (Subscriber_State[state],))
        
        subscribers = [dict(row) for row in cursor.fetchall()]
        
        log.debug(f"Fetched {len(subscribers)} {state} subscribers with {lang} language")
        return subscribers

def get_subscriber(email):
    """
    Retrieve a single user record by email
    
    This function queries the database for a user record based on the email address.
    If a matching user is found, returns a dictionary containing the user information;
    otherwise, returns None.
    
    Args:
        email (str): The email address to query
        
    Returns:
        dict or None: A dictionary containing user information 
        if found, None otherwise.
        The dictionary includes all the fields in the 
        db_tables['user'] table.
    """
    if not email or not isinstance(email, str):
        log.warning("Invalid email provided to get_user")
        return None
        
    with get_db_connection() as conn:
        cursor = conn.execute(f"""
            SELECT * 
            FROM {db_tables['user']} 
            WHERE email = ?
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            user = dict(result)
            log.debug(f"Found user: {user['email']}")
            return user
            
    log.debug(f"No user found with email: {email}")
    return None

def add_or_update_user(user_data, update=False):
    """
    Add or update a user in the db_table['user'] table,
    depending on the value of update.
    
    Args:
        user_data (dict): Dictionary containing user information
        update (bool, optional): Whether to update an existing user. Defaults to False.
    
    Returns:
        int: The ID of the newly created/updated user if successful, None otherwise
    """
    if not user_data or not isinstance(user_data, dict):
        log.error("No user data provided or invalid format")
        return None
    if not user_data.get('email'):
        log.error("Missing required fields for user update")
        return None
    if update:
        # get user_id by email
        user_rcd = get_subscriber(user_data['email'])
        if not user_rcd:
            log.error("Missing required fields for user update")
            return None
        return update_user(user_rcd['id'], user_data)
    else:
        if not user_data.get('is_active') or not user_data.get('l10n'):
            log.error("Missing required fields for user creation")
            return None
        return create_user(user_data['email'], user_data['is_active'], user_data['l10n'])

def update_user(user_id, update_fields):
    """
    Update user information with the given fields.
    
    Args:
        user_id (int): The ID of the user to update
        update_fields (dict): Dictionary of fields to update with their new values
                             Example: {'email': 'new@example.com', 'l10n': 'US'}
        
    Returns:
        int: The ID of the updated user if successful, None otherwise
    """
    if not isinstance(user_id, int) or user_id <= 0:
        log.error(f"Invalid user ID provided for update: {user_id}")
        return None
        
    if not update_fields or not isinstance(update_fields, dict):
        log.error("No update fields provided or invalid format")
        return None
        
    # Remove any None values and create a clean update dictionary
    clean_updates = {k: v for k, v in update_fields.items() if v is not None}
    if not clean_updates:
        log.warning("No valid fields to update")
        return None
        
    # Get the list of columns from the user table
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({db_tables['user']})")
        table_columns = {row[1] for row in cursor.fetchall()}  # Get all column names
    
    # Remove 'id' and 'created_at' as they shouldn't be updated
    table_columns.discard('id')
    table_columns.discard('created_at')
    
    # Filter out any fields that aren't in the table columns
    valid_updates = {k: v for k, v in clean_updates.items() 
                    if k in table_columns and v is not None}
                    
    if not valid_updates:
        log.error(f"No valid fields to update. Allowed fields: {table_columns}")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Build the SET clause dynamically
            set_clause = ", ".join(f"{field} = ?" for field in valid_updates.keys())
            values = list(valid_updates.values())
            values.append(user_id)  # Add user_id for the WHERE clause
            
            sql = f"""
                UPDATE {db_tables['user']}
                SET {set_clause}
                WHERE id = ?
            """
            
            log.debug(f"Executing: {sql} with values: {values}")
            cursor.execute(sql, values)
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                log.info(f"Successfully updated user ID {user_id} with fields: {list(valid_updates.keys())}")
                return user_id
            else:
                log.warning(f"No user found with ID: {user_id}")
                return None
                
    except sqlite3.IntegrityError as e:
        log.error(f"Integrity error while updating user ID {user_id}: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            log.error("Email address already exists in the system")
        return None
    except sqlite3.Error as e:
        log.error(f"Database error while updating user ID {user_id}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Unexpected error while updating user ID {user_id}: {str(e)}")
        return None

def create_user(email, state, lang=None):
    """
    Create a new user in the db_table['user'] table with the key
    of email.
    
    Args:
        email (str): User's email address (must be unique)
        state (int): user state (see Subscriber_State values)
        lang (str, optional): User's preferred language code. Defaults to None.
        
    Returns:
        int or None: The ID of the newly created user if successful, None otherwise
        
    Example:
        >>> user_id = create_user("user@example.com", Subscriber_State['active'], "en")
        >>> print(user_id)
        123
    """
    if not email or not isinstance(email, str):
        if not eu.validate_email(email):
            log.error("Invalid email provided")
            return None
        
    if state not in Subscriber_State.values():
        log.error(f"Invalid state provided: {state}")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user with this email already exists
            cursor.execute(f"""
                SELECT id FROM {db_tables['user']} 
                WHERE email = ?
            """, (email,))
            
            if cursor.fetchone() is not None:
                log.warning(f"User with email {email} already exists")
                return None
                
            # Insert new user
            cursor.execute(f"""
                INSERT INTO {db_tables['user']} 
                (email, is_active, l10n, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
            """, (email, state, lang))
            
            user_id = cursor.lastrowid
            conn.commit()
            log.info(f"Created new user with ID: {user_id}")
            return user_id
            
    except sqlite3.IntegrityError as e:
        log.error(f"Integrity error while creating user {email}: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            log.error("Email address already exists")
        return None
    except sqlite3.Error as e:
        log.error(f"Database error while creating user {email}: {str(e)}")
        return None
    except Exception as e:
        log.error(f"Unexpected error while creating user {email}: {str(e)}")
        return None

def get_users():
    """
    Fetch all users from the db_table['user'] table
    
    Returns:
        list: A list of dictionaries containing user information.
              Each dictionary has keys of all columns 
              in the db_table['user'] table
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {db_tables['user']} 
            ORDER BY id ASC
        """)
        users = [dict(row) for row in cursor.fetchall()]
        return users

def get_user_email(user_id):
    """
    Retrieve a user's email by their ID
    
    Args:
        user_id (int): The ID of the user
        
    Returns:
        str: The user's email if found, None otherwise
    """
    if not isinstance(user_id, int) or user_id <= 0:
        log.error(f"Invalid user ID provided: {user_id}")
        return None
        
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT email FROM {db_tables['user']} WHERE id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            log.warning(f"No user found with ID: {user_id}")
            return None
            
        except sqlite3.Error as e:
            log.error(f"Database error while retrieving email for user ID {user_id}: {str(e)}")
            return None
        except Exception as e:
            log.error(f"Unexpected error while retrieving email for user ID {user_id}: {str(e)}")
            return None

def delete_user(user_id):
    """
    Delete a user by their ID.
    
    Args:
        user_id (int): The ID of the user to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not isinstance(user_id, int) or user_id <= 0:
        log.error(f"Invalid user ID provided for deletion: {user_id}")
        return False
        
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['user']} WHERE id = ?"
            log.debug(f"Executing: {sql} with user_id: {user_id}")
            
            cursor.execute(sql, (user_id,))
            rows_affected = cursor.rowcount
            conn.commit()  # Commit the transaction
            
            if rows_affected > 0:
                log.info(f"Successfully deleted user with ID: {user_id}")
                return True
            else:
                log.warning(f"No user found with ID: {user_id}")
                return False
                
        except sqlite3.Error as e:
            log.error(f"Database error while deleting user ID {user_id}: {str(e)}")
            conn.rollback()
            return False
        except Exception as e:
            log.error(f"Unexpected error while deleting user ID {user_id}: {str(e)}")
            conn.rollback()
            return False

def delete_subscriber(email):
    """
    Delete a subscriber by email. 
    In fact, any user record can be deleted.
    
    Args:
        email (str): The email address of the subscriber to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not email:
        log.error("No email provided for deletion")
        return False
        
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['user']} WHERE email = ?"
            log.debug(f"Executing: {sql} with email: {email}")
            
            cursor.execute(sql, (email,))
            rows_affected = cursor.rowcount
            conn.commit()  # Commit the transaction
            
            if rows_affected > 0:
                log.info(f"Successfully deleted subscriber: {email}")
                return True
            else:
                log.warning(f"No subscriber found with email: {email}")
                return False
                
        except sqlite3.Error as e:
            log.error(f"Database error while deleting subscriber {email}: {str(e)}")
            conn.rollback()
            return False
        except Exception as e:
            log.error(f"Unexpected error while deleting subscriber {email}: {str(e)}")
            conn.rollback()
            return False

def get_articles(category, limit=None):
    """
    Retrieve a number (given by limit) of articles by category
    or all articles if limit is None given by category in 
    db_tables['article'] table and sorted by `updated_at` field
    in descending order.
    The category can be `all` to retrieve all articles without 
    specific category.
    The articles must be approved by admin review.
    
    Args:
        category (str): Article category to filter by, or 'all' to get articles from all categories
        limit (int, optional): Maximum number of articles to return. If None, returns all matching articles.
        
    Returns:
        list: A list of article information dictionaries, or None if no articles found.
              Each dictionary contains all columns of the 
              db_tables['article'] table.
    """
    if not category or category not in Article_Categories.values():
        log.warning(f"Invalid category '{category}' provided to get_articles. Must be one of: {', '.join(Article_Categories.values())}")
        return None
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f"""
            SELECT * FROM {db_tables['article']} 
            WHERE is_censored = ?
        """
        params = [Article_State['approved']]
        
        # Add category filter if not 'all'
        if category.lower() != 'all':
            query += " AND category = ?"
            params.append(category)
            
        # Always order by id in ascending order
        query += " ORDER BY id ASC"
        
        # Add limit if specified and valid
        if limit is not None and limit > 0:
            query += f" LIMIT {limit}"
        elif limit == 0:
            log.debug("Limit of 0 requested, returning no results")
            return []
            
        try:
            cursor.execute(query, tuple(params))
            articles = [dict(row) for row in cursor.fetchall()]
            return articles if articles else None
        except sqlite3.Error as e:
            log.error(f"Database error while retrieving articles: {str(e)}")
            return None
        except Exception as e:
            log.error(f"Unexpected error while retrieving articles: {str(e)}")
            return None

def get_articles_byDays(category, byDays=7):
    """
    Retrieve a number (given by previous byDays from today) of 
    articles, given by category, and sorted by `updated_at` field
    in descending order. 
    
    Args:
        category (str): Article category to filter by
        byDays (int, optional): Number of days to look back. Defaults to 7 days.
        
    Returns:
        list: A list of article information dictionaries from 
        the specified time period, or None if no articles found. 
        Each dictionary contains all columns of the 
        db_tables['article'] table.
    """
    if not category or category not in Article_Categories.values():
        log.warning(f"Invalid category '{category}' provided to get_articles_byDays. Must be one of: {', '.join(Article_Categories.keys())}")
        return None
        
    # Calculate date N days ago
    from datetime import datetime, timedelta
    days_ago = datetime.now() - timedelta(days=byDays)
    date_str = days_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {db_tables['article']} 
            WHERE is_censored = ?
            AND category = ? 
            AND updated_at >= ?
            ORDER BY updated_at DESC
        """, (Article_State['approved'], category, date_str))
        
        results = cursor.fetchall()
        if results:
            articles = []
            for result in results:
                article = dict(result)
                log.debug(f"Found article in category '{category}' from last {byDays} days: {article['id']}")
                articles.append(article)
            log.debug(f"Found {len(articles)} articles in category '{category}' from last {byDays} days")
            return articles
            
    log.debug(f"No articles found in category '{category}' from last {byDays} days")
    return None

def get_article_languages():
    """
    Retrieve all unique language codes (l10n) from articles
    
    Returns:
        list: A list of all unique language codes, sorted alphabetically
        
    Example:
        >>> languages = get_article_languages()
        >>> print(languages)
        ['en', 'zh', 'ja']
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT DISTINCT l10n 
                FROM {db_tables['article']}
                WHERE l10n IS NOT NULL
                ORDER BY l10n ASC
            """)
            
            # Extract the language codes from the query results
            languages = [row[0] for row in cursor.fetchall() if row[0]]
            
            log.debug(f"Found {len(languages)} unique language codes")
            return languages
            
    except sqlite3.Error as e:
        log.error(f"Error retrieving article languages: {e}")
        return []
    except Exception as e:
        log.error(f"Unexpected error in get_article_languages: {e}")
        return []
    
def get_article_categories():
    """
    Retrieve all unique article categories
    
    Returns:
        list: A list of all unique category names, sorted alphabetically
        
    Example:
        >>> categories = get_article_categories()
        >>> print(categories)
        ['Technology', 'Science', 'News']
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT DISTINCT category 
                FROM {db_tables['article']}
                ORDER BY category ASC
            """)
            
            # Convert result to a simple list
            categories = [row[0] for row in cursor.fetchall()]
            log.debug(f"Found {len(categories)} unique categories")
            return categories
            
    except sqlite3.Error as e:
        log.error(f"Error fetching article categories: {str(e)}")
        return []

def get_article_byId(article_id):
    """
    Retrieve a single article by its ID
    
    Args:
        article_id (int): The ID of the article to retrieve
        
    Returns:
        dict: A dictionary containing the article information, or None if not found.
              The dictionary includes the following keys:
              - id: Article ID
              - title: Article title
              - content: Article content
              - category: Article category
              - author: Author name
              - source: Source of the article
              - src_url: Source URL
              - image_url: URL of the article's image
              - l10n: Language/locale
              - created_at: Creation timestamp
              - updated_at: Last update timestamp
    """
    if not article_id or not isinstance(article_id, int) or article_id <= 0:
        log.warning(f"Invalid article ID provided: {article_id}")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {db_tables['article']}
                WHERE id = ?
            """, (article_id,))
            
            result = cursor.fetchone()
            if result:
                article = dict(result)
                log.debug(f"Found article with ID: {article_id}")
                return article
                
            log.debug(f"No article found with ID: {article_id}")
            return None
            
    except sqlite3.Error as e:
        log.error(f"Error fetching article with ID {article_id}: {str(e)}")
        return None

def get_next_article(article_id, category, is_censored=Article_State['pending']):
    """
    Retrieve the next article of given category to be reviewed
    
    Args:
        article_id (int): The ID of the article to retrieve
        category (str): The category of the article to retrieve
        is_censored (int): The state of the article to retrieve
        
    Returns:
        dict: A dictionary containing the article information, or None if not found.
              The dictionary includes the following keys:
              - id: Article ID
              - title: Article title
              - content: Article content
              - category: Article category
              - author: Author name
              - source: Source of the article
              - src_url: Source URL
              - image_url: URL of the article's image
              - l10n: Language/locale
              - created_at: Creation timestamp
              - updated_at: Last update timestamp
    """
    if not isinstance(article_id, int) or article_id <= 0:
        log.debug(f"Invalid article ID provided: {article_id}")
        return None
    cats = get_article_categories()
    if not isinstance(category, str) or category not in cats:
        log.debug(f"Invalid article category provided: {category}")
        return None
    if not isinstance(  is_censored, int) or is_censored not in Article_State.values():
        log.debug(f"Invalid article state provided: {is_censored}")
        return None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {db_tables['article']}
                WHERE is_censored = ?
                AND id >= ?
                AND category = ?
                ORDER BY id ASC
                LIMIT 1
            """, (is_censored, article_id, category))
            
            result = cursor.fetchone()
            if result:
                article = dict(result)
                log.debug(f"Found article with ID: {article['id']}")
                return article['id'], article
                
            log.debug(f"No article found with state: {is_censored}")
            return None
            
    except sqlite3.Error as e:
        log.error(f"Error fetching article with state {is_censored}: {str(e)}")
        return None
    
def review_article(article_id, is_censored, category=None):
    """
    Review an article by its ID
    
    Args:
        article_id (int): The ID of the article to review
        is_censored (int): The state of the article to set/reset
        category (str): The category of the article to classify
        
    Returns:
        bool: True if review was successful, False otherwise
    """
    if not article_id or not isinstance(article_id, int) or article_id <= 0:
        log.debug(f"Invalid article ID provided: {article_id}")
        return False
    if get_article_byId(article_id) is None:
        log.debug(f"No article found with ID: {article_id}")
        return False
    if  is_censored not in Article_State.values():
        log.debug(f"Invalid article state provided: {is_censored}")
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if category is None:
                cursor.execute(f"""
                        UPDATE {db_tables['article']}
                        SET is_censored = ?
                        WHERE id = ?
                        """, (is_censored, article_id))
            else:
                cursor.execute(f"""
                        UPDATE {db_tables['article']}
                        SET is_censored = ?, category = ?
                        WHERE id = ?
                        """, (is_censored, category, article_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"Successfully set article state to {is_censored} for article with ID: {article_id}")
                return True
            else:
                log.debug(f"No article found with ID: {article_id}")
                return False
                
    except sqlite3.Error as e:
        log.error(f"Error setting article state to {is_censored} for article with ID {article_id}: {str(e)}")
        return False
    
def add_or_update_article(article_data, update=False):
    """
    Create a new article or update an existing article 
    in the db_table['article'] table, depending on the
    value of the `update` parameter.
    If `update` is True, update the article with the given `title`.
    If `update` is False, create a new article. return error if 
    `title` exists.
    
    Args:
        article_data (dict): Article data containing fields that are
        specified in the db_table['article'] table.
        update (bool): Whether to update an existing article or create a new one.
        
    Returns:
        int or None: The ID of the newly created/updated article if successful, None otherwise
    """
    if not article_data or 'title' not in article_data:
        log.error("Missing required article data or title")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            
            # dynamically get table columns from article table
            cursor.execute(f"PRAGMA table_info({db_tables['article']})")       
            table_columns = {row[1] for row in cursor.fetchall()}  # Get all column names
            
            # Remove 'id' and 'created_at' as they shouldn't be updated
            table_columns.discard('id')
            table_columns.discard('created_at')

            # Check if article with this title already exists
            cursor.execute(f"""
                SELECT id FROM {db_tables['article']} 
                WHERE title = ?
            """, (article_data['title'],))
            
            existing_article = cursor.fetchone()
            
            if existing_article:
                if not update:
                    log.error(f"Article with title '{article_data['title']}' already exists")
                    return None
                
                # Update existing article
                article_id = existing_article['id']
                update_fields = []
                params = []
                
                # Build update fields dynamically from article_data
                for field in article_data:
                    if field in table_columns:
                        update_fields.append(f"{field} = ?")
                        params.append(article_data[field])
                
                # Add is_censored if not provided, default to pending
                if 'is_censored' not in article_data:
                    update_fields.append("is_censored = ?")
                    params.append(Article_State['pending'])
                
                # Build and execute update query
                update_query = f"""
                    UPDATE {db_tables['article']}
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """
                params.append(article_id)
                
                cursor.execute(update_query, params)
                conn.commit()
                log.info(f"Successfully updated article ID: {article_id}")
                return article_id
            
            else:
                # Insert new article
                required_fields = ['title', 'content', 'category', 'author', 'source']
                for field in required_fields:
                    if field not in article_data:
                        log.error(f"Missing required field: {field}")
                        return None
                
                # Prepare data for insertion
                # Set default values for optional fields
                defaults = {
                    'src_url': '',
                    'image_url': '',
                    'user_id': 0,
                    'l10n': 'US',
                    'is_censored': Article_State['pending']
                }
                
                # Use provided values or defaults
                values = []
                placeholders = []
                fields = []
                for field in article_data:
                    if field in table_columns:
                        value = article_data.get(field, defaults.get(field))
                        values.append(value)
                        placeholders.append('?')
                        fields.append(field)
                
                # Build and execute insert query
                insert_query = f"""
                    INSERT INTO {db_tables['article']} 
                    ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(insert_query, values)
                article_id = cursor.lastrowid
                conn.commit()
                log.info(f"Successfully created article with ID: {article_id}")
                return article_id
            
    except sqlite3.Error as e:
        log.error(f"Database error in add_or_update_article: {str(e)}")
        return None

def delete_article(article_id):
    """
    Delete an article by its ID
    
    Args:
        article_id (int): The ID of the article to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not article_id or not isinstance(article_id, int) or article_id <= 0:
        log.debug(f"Invalid article ID provided: {article_id}")
        return False
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {db_tables['article']}
                WHERE id = ?
            """, (article_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"Successfully deleted article with ID: {article_id}")
                return True
            else:
                log.debug(f"No article found with ID: {article_id}")
                return False
                
    except sqlite3.Error as e:
        log.error(f"Error deleting article with ID {article_id}: {str(e)}")
        return False
    
def drop_table(tbl):
    """
    Drop the specified database table
    
    Args:
        tbl (str): Name of the table to drop
    
    Returns:
        bool: True if the table was successfully dropped, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
            if cursor.fetchone() is None:
                log.debug(f"Table '{tbl}' does not exist")
                return False
                
            # Drop table
            cursor.execute(f"DROP TABLE {db_tables[tbl]}")
            conn.commit()
            log.info(f"Successfully dropped table '{tbl}'")

            return True
            
    except sqlite3.Error as e:
        log.error(f"Error dropping table '{tbl}': {str(e)}")
        return False
    
def import_subscribers(subscribers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Import subscribers into the db_tables['user'] table.
    
    If a subscriber already exists (based on email), update 
    the following fields:
    - is_active 
    - l10n
    
    If the subscriber does not exist, insert a new subscriber with 
    the following fields:
    - email
    - is_active
    - l10n
    - token
    - password_hash
    - salt
    - created_at
    
    Args:
        subscribers: List of subscriber dictionaries with required fields:
            - email (str): Subscriber's email address (required)
            - is_active (int, optional): Subscription status (default: inactive)
            - l10n (str, optional): Language/locale (default: 'US')
            - token (str, optional): Authentication token (default: '')
            - password_hash (str, optional): Hashed password (default: '')
            - salt (str, optional): Password salt (default: '')
            - created_at (str, optional): Creation timestamp (default: current time)
        
    Returns:
        Dict with import results:
        {
            'success': bool,  # True if no errors occurred
            'imported': int,  # Number of successfully imported subscribers
            'skipped': int,   # Number of skipped subscribers (due to errors)
            'errors': List[str]  # List of error messages if any
        }
    """
    imported = 0
    skipped = 0
    errors = []
    
    # Ensure we have a list of subscribers
    if not isinstance(subscribers, list):
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': ['Subscribers must be provided as a list of dictionaries']
        }
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for i, sub in enumerate(subscribers, 1):
            try:
                if not isinstance(sub, dict):
                    errors.append(f'Subscriber {i}: Expected a dictionary, got {type(sub).__name__}')
                    skipped += 1
                    continue
                    
                email = sub.get('email')
                if not email:
                    errors.append(f'Subscriber {i}: Missing required field "email"')
                    skipped += 1
                    continue
                    
                # Check if subscriber exists
                cursor.execute(
                    f'SELECT id FROM {db_tables["user"]} WHERE email = ?',
                    (email,)
                )
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing subscriber
                    cursor.execute(f"""
                        UPDATE {db_tables['user']}
                        SET is_active = ?,
                            l10n = ?
                        WHERE email = ?
                    """, (
                        int(sub.get('is_active', Subscriber_State['inactive'])),
                        sub.get('l10n', 'US'),
                        email
                    ))
                    imported += 1
                    log.debug(f'Updated subscriber: {email}')
                else:
                    # Insert new subscriber with all required fields
                    cursor.execute(f"""
                        INSERT INTO {db_tables['user']} (
                            email, is_active, l10n, token,
                            password_hash, salt, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        email,
                        int(sub.get('is_active', Subscriber_State['inactive'])),
                        sub.get('l10n', 'US'),
                        sub.get('token', ''),
                        sub.get('password_hash', ''),
                        sub.get('salt', ''),
                        sub.get('created_at', datetime.now())
                    ))
                    imported += 1
                    log.debug(f'Imported new subscriber: {email}')
                    
            except Exception as e:
                error_msg = f'Error importing subscriber {i} ({email or "unknown"}): {str(e)}'
                errors.append(error_msg)
                skipped += 1
                log.error(error_msg, exc_info=True)
        
        try:
            conn.commit()
        except Exception as e:
            error_msg = f'Database commit error: {str(e)}'
            errors.append(error_msg)
            log.error(error_msg, exc_info=True)
            return {
                'success': False,
                'imported': 0,
                'skipped': len(subscribers),
                'errors': errors
            }
        
    return {
        'success': len(errors) == 0,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }
    
def import_users(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Import users into the db_tables['user'] table.
    
    Args:
        users: List of user dictionaries with all the fields,
        except `updated_at` field
            
    Returns:
        Dict with import results
    """
    imported = 0
    skipped = 0
    errors = []
    
    with get_db_connection() as conn:
        for i, user in enumerate(users, 1):
            try:
                # Prepare user data for add_user function
                user_data = {
                    'email': user.get('email'),
                    'password_hash': user.get('password_hash'),
                    'salt': user.get('salt'),
                    'is_active': user.get('is_active', Subscriber_State['inactive']),
                    'l10n': user.get('l10n', 'US'),
                    'token': user.get('token')
                }
                
                # Use add_or_update_user to add or update users
                user_id = add_or_update_user(user_data, update=True)
                if user_id:
                    imported += 1
                    conn.commit()
                else:
                    errors.append(f"User {i} ({user.get('email', 'unknown')}): Failed to update user")
                    skipped += 1
                
            except Exception as e:
                errors.append(f"Error importing user {i} ({user.get('email', 'unknown')}): {str(e)}")
                skipped += 1
                conn.rollback()
    
    return {
        'success': len(errors) == 0,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }   
    
def import_articles(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Import articles into the db_tables['article'] table.
    
    Args:
        articles: List of article dictionaries with all the fields,
        except `updated_at` field
            
    Returns:
        Dict with import results
    """
    imported = 0
    skipped = 0
    errors = []
    
    with get_db_connection() as conn:
        for i, article in enumerate(articles, 1):
            try:
                # Prepare article data for add_article function
                article_data = {
                    'title': article.get('title'),
                    'content': article.get('content', ''),
                    'category': article.get('category', Article_Categories['news']),
                    'author': article.get('author'),
                    'source': article.get('source'),
                    'src_url': article.get('src_url'),
                    'image_url': article.get('image_url'),
                    'l10n': article.get('l10n', 'US'),
                    'user_id': article.get('user_id', 0),
                    'is_censored': article.get('is_censored', Article_State['pending'])
                }
                    
                # Use add_article to add or update articles
                article_id = add_or_update_article(article_data, update=True)
                if article_id:
                    imported += 1
                    conn.commit()
                else:
                    errors.append(f"Article {i} ({article.get('title', 'unknown')}): Failed to update article")
                    skipped += 1
            except Exception as e:
                errors.append(f"Error importing article {i} ({article.get('title', 'unknown')}): {str(e)}")
                skipped += 1
                conn.rollback()
    
    return {
        'success': len(errors) == 0,
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    }
        
def import_from_file(file_path: Union[str, Path], table: str) -> Dict[str, Any]:
    """
    Import records from a JSON or CSV file into the specified table.
    
    Args:
        file_path: Path to the JSON or CSV file containing records data
        db_connection: SQLite database connection object
        
    Returns:
        Dict with import results: {
            'success': bool,
            'imported': int,
            'skipped': int,
            'errors': List[str]
        }
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [f"File not found: {file_path}"]
        }
    
    try:
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                rcds = json.load(f)
                if not isinstance(rcds, list):
                    rcds = [rcds]  # Handle single user object
        elif file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rcds = list(reader)
        else:
            return {
                'success': False,
                'imported': 0,
                'skipped': 0,
                'errors': ["Unsupported file format. Please use JSON or CSV."]
            }
        if table == db_tables['user']:
            return import_users(rcds)
        elif table == db_tables['article']:
            return import_articles(rcds)
        elif table == db_tables['subscriber']:
            return import_subscribers(rcds)
        else:
            return {
                'success': False,
                'imported': 0,
                'skipped': 0,
                'errors': [f"Unsupported table: {table}"]
        }
    
    except Exception as e:
        return {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [f"Error reading file: {str(e)}"]
        }

def export_to_file(file_path: Union[str, Path], table: str) -> Dict[str, Any]:
    """
    Export a table from the database to a JSON or CSV file.
    
    Args:
        file_path: Path to save the exported file (must end with .json or .csv)
        table: Name of the table to export
        
    Returns:
        Dict with export results
        {
            'success': bool,
            'message': str,
            'file_path': str,
            'count': int
        }
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if table == db_tables['user']:
            rcds = get_users()
        elif table == db_tables['article']:
            rcds = get_articles('all')
        elif table == db_tables['subscriber']:
            rcds = get_subscribers(state='all')
        else:
            return {
                'success': False,
                'message': "Unsupported table. Please use user, article, or subscriber",
                'file_path': str(file_path.absolute()),
                'count': 0
            }
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rcds, f, indent=2, ensure_ascii=False)
        elif file_path.suffix.lower() == '.csv':
            if rcds:
                fieldnames = rcds[0].keys()
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rcds)
        else:
            return {
                'success': False,
                'message': "Unsupported file format. Please use .json or .csv",
                'file_path': str(file_path.absolute()),
                'count': 0
            }
        
        return {
            'success': True,
            'message': f"Successfully exported {len(rcds)} records to {file_path}",
            'file_path': str(file_path.absolute()),
            'count': len(rcds)
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f"Error exporting records: {str(e)}",
            'file_path': str(file_path.absolute()),
            'count': 0
        }

def get_total_records(table: str) -> int:
    """
    Get the total number of records in a table.
    
    Args:
        table: Name of the table to query
        
    Returns:
        int: Total number of records in the table
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            result = cursor.fetchone()
            return result[0] if result else 0
    except sqlite3.Error as e:
        log.error(f"Database error fetching total records: {str(e)}")
        raise sqlite3.Error(f"Failed to fetch total records: {str(e)}")
    
# Initialize the database when this module is imported
init_db()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create data directory
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Test database connection first
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("\nDatabase tables:")
            for table in tables:
                print(f"- {table[0]}")
            
            # Check if user table exists
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{db_tables['user']}'")
            if cursor.fetchone()[0] == 0:
                print(f"\nERROR: Table '{db_tables['user']}' does not exist in the database!")
                exit(1)
                
    except Exception as e:
        print(f"\nERROR: Failed to connect to database: {str(e)}")
        exit(1)
    
    # Export users
    # json_path = os.path.join(data_dir, 'users_backup.json')
    # csv_path = os.path.join(data_dir, 'users_backup.csv')
    
    # print(f"\nExporting users to {json_path}")
    # if export_users_to_file(json_path, 'json'):
    #     print(f"✓ Successfully exported to {json_path}")
    # else:
    #     print(f"✗ Failed to export to {json_path}")
    
    # print(f"\nExporting users to {csv_path}")
    # if export_users_to_file(csv_path, 'csv'):
    #     print(f"✓ Successfully exported to {csv_path}")
    # else:
    #     print(f"✗ Failed to export to {csv_path}")
        
    # Import users
    # json_path = os.path.join(data_dir, 'users_backup.json')
    # csv_path = os.path.join(data_dir, 'users_backup.csv')
    
    # import users from JSON
    # print(f"\nImporting users from {json_path}")
    # success, errors, skipped = import_users_from_file(json_path, 'json')
    # print(f"Import from JSON: Success: {success}, Errors: {errors}, Skipped: {skipped}")
   
    # import users from CSV
    # print(f"\nImporting users from {csv_path}")
    # success, errors, skipped = import_users_from_file(csv_path, 'csv')
    # print(f"Import from CSV: Success: {success}, Errors: {errors}, Skipped: {skipped}")
    
    # export articles to JSON
    # json_path = os.path.join(data_dir, 'articles_backup.json')
    # if export_articles_to_file(json_path, 'json'):
    #     print(f"✓ Successfully exported to {json_path}")
    # else:
    #     print(f"✗ Failed to export to {json_path}")

    # export articles to CSV
    # csv_path = os.path.join(data_dir, 'articles_backup.csv')
    # if export_articles_to_file(csv_path, 'csv'):
    #     print(f"✓ Successfully exported to {csv_path}")
    # else:
    #     print(f"✗ Failed to export to {csv_path}")
    
    # import articles from JSON
    # json_path = os.path.join(data_dir, 'articles_backup.json')
    # success, errors, skipped = import_articles_from_file(json_path, 'json')
    # print(f"Import from JSON: Success: {success}, Errors: {errors}, Skipped: {skipped}")
    
    # import articles from CSV
    csv_path = os.path.join(data_dir, 'articles_backup.csv')
    success, errors, skipped = import_articles_from_file(csv_path, 'csv')
    print(f"Import from CSV: Success: {success}, Errors: {errors}, Skipped: {skipped}")