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
    "article": os.getenv("TBL_ARTICLE", "article")
    }
Subscriber_State = {
    'active': 1, 
    'pending': 0,
    'inactive': -1
    }
Article_State = {
    'approved': 1,
    'pending': 0,
    'rejected': -1
    }
# Values for Article categories
Article_Categories = {
    "news": "News", 
    "story": "Story", 
    "events": "Events", 
    "faq": "FAQ", 
    "about": "About",
    "contact": "Contact",
    "feedback": "Feedback"
    }

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(dbn)
    conn.row_factory = sqlite3.Row
    return conn

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
            is_censored INTEGER DEFAULT 0
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        
        # Create triggers to automatically update the updated_at timestamp
        for table_name in [db_tables['user'], db_tables['article']]:
            # First drop the trigger if it exists
            try:
                conn.execute(f"DROP TRIGGER IF EXISTS update_{table_name}_timestamp")
            except sqlite3.OperationalError as e:
                if "no such table" not in str(e):
                    raise
            
            # Create the new trigger
            trigger_sql = f"""
            CREATE TRIGGER update_{table_name}_timestamp
            AFTER UPDATE ON {table_name}
            FOR EACH ROW
            BEGIN
                UPDATE {table_name} 
                SET updated_at = datetime('now')
                WHERE rowid = NEW.rowid;
            END;
            """
            try:
                conn.execute(trigger_sql)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    raise
        
        conn.commit()

def add_subscriber(email, token, lang=None):
    """Add a new subscriber with pending status 
    or update existing one with active status"""
    with get_db_connection() as conn:
        try:
            if lang:
                conn.execute(f'''
                INSERT INTO {db_tables['user']} (email, token, is_active, l10n, created_at)
                VALUES (?, ?, {Subscriber_State['pending']}, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {Subscriber_State['active']},
                token = excluded.token,
                l10n = excluded.l10n,
                updated_at = CURRENT_TIMESTAMP
                ''', (email, token, lang))
            else:
                conn.execute(f'''
                INSERT INTO {db_tables['user']} (email, token, is_active, created_at)
                VALUES (?, ?, {Subscriber_State['pending']}, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {Subscriber_State['active']},
                token = excluded.token,
                updated_at = CURRENT_TIMESTAMP
                ''', (email, token))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

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
    Fetch subscribers from the database based on their status
    
    Args:
        state (str): Filter subscribers by state. 
            'active' - only active subscribers (default)
            'inactive' - only inactive subscribers
            'pending' - only pending subscribers
            'all' - all subscribers regardless of subscriber state and language 
    
    Returns:
        list: A list of dictionaries containing subscriber information.
              Each dictionary has keys: id, email, token, is_active, created_at, updated_at
    """
    # Validate status parameter
    if state not in ('active', 'inactive', 'pending', 'all'):
        raise ValueError("state must be 'active', 'inactive', 'pending', or 'all'")
    
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row  # This enables column access by name
        
        # Build the query based on status
        if state == 'all':
            cursor = conn.execute(f"""
            SELECT * FROM {db_tables['user']} 
            ORDER BY created_at DESC
        """)
        else:
            if lang:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['user']} 
                WHERE is_active = ? AND l10n = ?
                ORDER BY created_at DESC
            """, (Subscriber_State[state], lang))
            else:
                cursor = conn.execute(f"""
                SELECT * FROM {db_tables['user']} 
                WHERE is_active = ?
                ORDER BY created_at DESC
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
        dict or None: A dictionary containing user information if found, None otherwise.
                     The dictionary includes the following keys:
                     - id: Unique user identifier
                     - email: Email address
                     - token: Verification token
                     - is_active: Account status (1/0/-1)
                     - l10n: Language/locale
                     - created_at: Creation timestamp
                     - updated_at: Last update timestamp
    """
    if not email or not isinstance(email, str):
        log.warning("Invalid email provided to get_user")
        return None
        
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
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

def update_user(user_id, update_fields):
    """
    Update user information with the given fields.
    
    Args:
        user_id (int): The ID of the user to update
        update_fields (dict): Dictionary of fields to update with their new values
                             Example: {'email': 'new@example.com', 'l10n': 'US'}
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    if not isinstance(user_id, int) or user_id <= 0:
        log.error(f"Invalid user ID provided for update: {user_id}")
        return False
        
    if not update_fields or not isinstance(update_fields, dict):
        log.error("No update fields provided or invalid format")
        return False
        
    # Remove any None values and create a clean update dictionary
    clean_updates = {k: v for k, v in update_fields.items() if v is not None}
    if not clean_updates:
        log.warning("No valid fields to update")
        return False
        
    # List of allowed fields that can be updated
    allowed_fields = {'email', 'is_active', 'l10n'}
    
    # Filter out any fields that aren't in the allowed set
    valid_updates = {k: v for k, v in clean_updates.items() 
                    if k in allowed_fields and v is not None}
                    
    if not valid_updates:
        log.error(f"No valid fields to update. Allowed fields: {allowed_fields}")
        return False
        
    try:
        with get_db_connection() as conn:
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
            cursor = conn.cursor()
            cursor.execute(sql, values)
            rows_affected = cursor.rowcount
            conn.commit()
            
            if rows_affected > 0:
                log.info(f"Successfully updated user ID {user_id} with fields: {list(valid_updates.keys())}")
                return True
            else:
                log.warning(f"No user found with ID: {user_id}")
                return False
                
    except sqlite3.IntegrityError as e:
        log.error(f"Integrity error while updating user ID {user_id}: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            log.error("Email address already exists in the system")
        return False
    except sqlite3.Error as e:
        log.error(f"Database error while updating user ID {user_id}: {str(e)}")
        return False
    except Exception as e:
        log.error(f"Unexpected error while updating user ID {user_id}: {str(e)}")
        return False


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
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['user']} WHERE id = ?"
            log.debug(f"Executing: {sql} with user_id: {user_id}")
            
            cursor = conn.cursor()
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
            # Use parameterized query to prevent SQL injection
            sql = f"DELETE FROM {db_tables['user']} WHERE email = ?"
            log.debug(f"Executing: {sql} with email: {email}")
            
            cursor = conn.cursor()
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
    Retrieve the latest articles by category
    
    Args:
        category (str): Article category to filter by
        limit (int, optional): Maximum number of articles to return
        
    Returns:
        list: A list of article information dictionaries, or None if no articles found.
              Each dictionary contains the following keys:
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
    if not category:
        log.warning("No category provided to get_article")
        return None
        
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        if limit is None:
            cursor = conn.execute(f"""
                SELECT * FROM {db_tables['article']} 
                WHERE is_censored = 1 
                AND category = ?
                ORDER BY id ASC
                """, (category,))
        elif limit > 0:
            cursor = conn.execute(f"""
                SELECT * FROM {db_tables['article']} 
                WHERE is_censored = 1 
                AND category = ?
                ORDER BY id ASC
                LIMIT {limit}
                """, (category,))
        else:
            log.debug(f"Invalid limit value: {limit}")
            return None
        
        results = cursor.fetchall()
        if results:
            articles = []
            for result in results:
                article = dict(result)
                log.debug(f"Found article in category '{category}': {article['id']}")
                articles.append(article)
            log.debug(f"Found articles in category '{category}': {articles}")
            return articles
            
    log.debug(f"No article found in category: {category}")
    return None

def get_articles_byDays(category, byDays=7):
    """
    Retrieve articles from the last N days by category,
    sorted by updated_at in descending order
    
    Args:
        category (str): Article category to filter by
        byDays (int, optional): Number of days to look back. Defaults to 7 days.
        
    Returns:
        list: A list of article information dictionaries from the specified time period,
              or None if no articles found. Each dictionary contains:
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
    if not category:
        log.warning("No category provided to get_articles_byDays")
        return None
        
    # Calculate date N days ago
    from datetime import datetime, timedelta
    days_ago = datetime.now() - timedelta(days=byDays)
    date_str = days_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"""
            SELECT * FROM {db_tables['article']} 
            WHERE is_censored = 1
            AND category = ? 
            AND updated_at >= ?
            ORDER BY updated_at DESC
        """, (category, date_str))
        
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
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
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
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
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
    
def review_article(article_id, is_censored):
    """
    Review an article by its ID
    
    Args:
        article_id (int): The ID of the article to review
        is_censored (int): The state of the article to set/reset
        
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
            cursor.execute(f"""
                UPDATE {db_tables['article']}
                SET is_censored = ?
                WHERE id = ?
            """, (is_censored, article_id))
            
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
    
def create_article(title, content, category, author, source, src_url=None, image_url=None, l10n='US'):
    """
    Create a new article in the database
    
    Args:
        title (str): Article title
        content (str): Article content (can include HTML)
        category (str): Article category (e.g., 'News', 'Story', 'Events', 'FAQ', 'About')
        author (str): Author's name
        source (str): Source of the article
        src_url (str, optional): URL to the original article
        image_url (str, optional): URL to an image for the article
        l10n (str, optional): Language/locale code. Defaults to 'US'.
        
    Returns:
        int or None: The ID of the newly created article if successful, None otherwise
    """
    if not all([title, content, category, author, source]):
        log.debug("Missing required article fields")
        return None
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {db_tables['article']} (
                    title, content, category, author, 
                    source, src_url, image_url, l10n,
                    created_at, updated_at, is_censored
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, content, category, author,
                source, src_url, image_url, l10n,
                datetime.datetime.now(), 
                datetime.datetime.now(), 
                Article_State['pending']
            ))
            
            article_id = cursor.lastrowid
            conn.commit()
            log.info(f"Successfully created article with ID: {article_id}")
            return article_id
            
    except sqlite3.Error as e:
        log.error(f"Error creating article: {str(e)}")
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
    
def export_users_to_file(file_path, format_type='json'):
    """
    Export all users from the database to a file in JSON or CSV format.
    
    Args:
        file_path (str): Path where the file will be saved
        format_type (str): Output format - 'json' or 'csv'
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {db_tables['user']}")
            users = cursor.fetchall()
            
            if not users:
                log.warning("No users found to export")
                return False
                
            # Convert to list of dicts
            user_list = [dict(user) for user in users]
            
            if format_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(user_list, f, indent=2, default=str)
            elif format_type.lower() == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=user_list[0].keys())
                    writer.writeheader()
                    writer.writerows(user_list)
            else:
                log.error(f"Unsupported format: {format_type}. Use 'json' or 'csv'")
                return False
                
            log.info(f"Successfully exported {len(user_list)} users to {file_path}")
            return True
            
    except Exception as e:
        log.error(f"Error exporting users: {str(e)}")
        return False

def export_articles_to_file(file_path, format_type='json'):
    """
    將所有文章從資料庫匯出為 JSON 或 CSV 格式的檔案。
    
    參數:
        file_path (str): 檔案儲存路徑
        format_type (str): 輸出格式 - 'json' 或 'csv'
        
    回傳:
        bool: 匯出成功回傳 True，失敗回傳 False
    """
    try:
        # 如果目錄不存在則建立
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {db_tables['article']}")
            articles = cursor.fetchall()
            
            if not articles:
                log.warning("沒有找到要匯出的文章")
                return False
                
            # 轉換為字典列表
            article_list = [dict(article) for article in articles]
            
            if format_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(article_list, f, indent=2, default=str, ensure_ascii=False)
            elif format_type.lower() == 'csv':
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=article_list[0].keys())
                    writer.writeheader()
                    writer.writerows(article_list)
            else:
                log.error(f"不支援的格式: {format_type}。請使用 'json' 或 'csv'")
                return False
                
            log.info(f"成功匯出 {len(article_list)} 篇文章至 {file_path}")
            return True
            
    except Exception as e:
        log.error(f"匯出文章時發生錯誤: {str(e)}")
        return False


def import_users_from_file(file_path, format_type='json'):
    """
    Import users from a JSON or CSV file into the database.
    Skips users that already exist (based on email).
    
    Args:
        file_path (str): Path to the import file
        format_type (str): Input format - 'json' or 'csv'
        
    Returns:
        tuple: (success_count, error_count, skipped_count)
    """
    success = 0
    errors = 0
    skipped = 0
    
    if not os.path.exists(file_path):
        log.error(f"File not found: {file_path}")
        return 0, 1, 0
        
    try:
        users = []
        if format_type.lower() == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
        elif format_type.lower() == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                users = list(csv.DictReader(f))
        else:
            log.error(f"Unsupported format: {format_type}. Use 'json' or 'csv'")
            return 0, 1, 0
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for user in users:
                try:
                    # Check if user already exists
                    cursor.execute(
                        f"SELECT id FROM {db_tables['user']} WHERE email = ?",
                        (user['email'],)
                    )
                    if cursor.fetchone():
                        log.debug(f"User {user['email']} already exists, skipping")
                        skipped += 1
                        continue
                        
                    # Insert new user
                    cursor.execute(f"""
                        INSERT INTO {db_tables['user']} 
                        (email, token, is_active, l10n, created_at, updated_at)
                        VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), 
                        COALESCE(?, CURRENT_TIMESTAMP))
                    """, (
                        user.get('email'),
                        user.get('token', ''),
                        int(user.get('is_active', 0)),
                        user.get('l10n', 'US'),
                        user.get('created_at'),
                        user.get('updated_at')
                    ))
                    success += 1
                    log.debug(f"Imported user: {user.get('email')}")
                    
                except Exception as e:
                    errors += 1
                    log.error(f"Error importing user {user.get('email')}: {str(e)}")
            
            conn.commit()
            
        log.info(f"Import completed. Success: {success}, Errors: {errors}, Skipped: {skipped}")
        return success, errors, skipped
        
    except Exception as e:
        log.error(f"Error importing users: {str(e)}")
        return success, errors + 1, skipped
    
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
    json_path = os.path.join(data_dir, 'users_backup.json')
    csv_path = os.path.join(data_dir, 'users_backup.csv')
    
    print(f"\nExporting users to {json_path}")
    if export_users_to_file(json_path, 'json'):
        print(f"✓ Successfully exported to {json_path}")
    else:
        print(f"✗ Failed to export to {json_path}")
    
    print(f"\nExporting users to {csv_path}")
    if export_users_to_file(csv_path, 'csv'):
        print(f"✓ Successfully exported to {csv_path}")
    else:
        print(f"✗ Failed to export to {csv_path}")
        
    # Import users
    json_path = os.path.join(data_dir, 'users_backup.json')
    csv_path = os.path.join(data_dir, 'users_backup.csv')
    
    print(f"\nImporting users from {json_path}")
    success, errors, skipped = import_users_from_file(json_path, 'json')
    print(f"Import from JSON: Success: {success}, Errors: {errors}, Skipped: {skipped}")
    
    success, errors, skipped = import_users_from_file(csv_path, 'csv')
    print(f"Import from CSV: Success: {success}, Errors: {errors}, Skipped: {skipped}")
    
    # export articles to JSON
    json_path = os.path.join(data_dir, 'articles_backup.json')
    if export_articles_to_file(json_path, 'json'):
        print(f"✓ Successfully exported to {json_path}")
    else:
        print(f"✗ Failed to export to {json_path}")

    # export articles to CSV
    csv_path = os.path.join(data_dir, 'articles_backup.csv')
    if export_articles_to_file(csv_path, 'csv'):
        print(f"✓ Successfully exported to {csv_path}")
    else:
        print(f"✗ Failed to export to {csv_path}")