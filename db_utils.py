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
from sre_parse import State
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
user_tbl = os.getenv("TBL_USR", "user")
article_tbl = os.getenv("TBL_ARTICLE", "article")
States = {
    'active': 1, 
    'pending': 0,
    'inactive': -1
    }

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(dbn)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        # create user table via SQL
        cmd = f"CREATE TABLE IF NOT EXISTS {user_tbl}"
        args = """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 0,
            l10n TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            token TEXT
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        conn.commit()
        
        # create article table via SQL
        cmd = f"CREATE TABLE IF NOT EXISTS {article_tbl}"
        args = """ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'News',
            author TEXT,
            source TEXT,
            src_url TEXT,
            image_url TEXT,
            l10n TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        conn.commit()

def add_subscriber(email, token, lang=None):
    """Add a new subscriber with pending status 
    or update existing one with active status"""
    with get_db_connection() as conn:
        try:
            if lang:
                conn.execute(f'''
                INSERT INTO {user_tbl} (email, token, is_active, l10n, created_at)
                VALUES (?, ?, {States['pending']}, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {States['active']},
                token = excluded.token,
                l10n = excluded.l10n,
                updated_at = CURRENT_TIMESTAMP
                ''', (email, token, lang))
            else:
                conn.execute(f'''
                INSERT INTO {user_tbl} (email, token, is_active, created_at)
                VALUES (?, ?, {States['pending']}, CURRENT_TIMESTAMP)
                ON CONFLICT(email) DO UPDATE SET
                    is_active = {States['active']},
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
            # Use 'inactive' state from States dictionary
            inactive_state = States['inactive']
            
            cursor.execute(f'''
            UPDATE {user_tbl} 
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
            SELECT id FROM {user_tbl} 
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
                     'all' - all subscribers regardless of status
    
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
            SELECT * FROM {user_tbl} 
            ORDER BY created_at DESC
        """)
        else:
            if lang:
                cursor = conn.execute(f"""
                SELECT * FROM {user_tbl} 
                WHERE is_active = ? AND l10n = ?
                ORDER BY created_at DESC
            """, (States[state], lang))
            else:
                cursor = conn.execute(f"""
                SELECT * FROM {user_tbl} 
                WHERE is_active = ?
                ORDER BY created_at DESC
            """, (States[state],))
        
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
            FROM {user_tbl} 
            WHERE email = ?
        """, (email,))
        
        result = cursor.fetchone()
        if result:
            user = dict(result)
            log.debug(f"Found user: {user['email']}")
            return user
            
    log.debug(f"No user found with email: {email}")
    return None

def delete_subscriber(email):
    """
    Always return None, even if the key does not exist.
    """
    with get_db_connection() as conn:
        cmd = f"DELETE FROM {user_tbl}" 
        where = f"WHERE email='{email}'"
        sql_stmt = f"{cmd} {where}"
        try:
            cursor = conn.cursor()
            cursor.execute(f"{sql_stmt}")
            log.debug(f"{sql_stmt}")
        except Exception as err:
            log.error(f"Caught '{err}'. class is {type(err)}")

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
                SELECT * FROM {article_tbl} 
                WHERE category = ?
                ORDER BY updated_at DESC
                """, (category,))
        elif limit > 0:
            cursor = conn.execute(f"""
                SELECT * FROM {article_tbl} 
                WHERE category = ?
                ORDER BY updated_at DESC
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
    Retrieve articles from the last N days by category
    
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
            SELECT * FROM {article_tbl} 
            WHERE category = ? 
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

def delete_article(article_id):
    """
    根據文章 ID 刪除文章
    
    參數:
        article_id (int): 要刪除的文章 ID
        
    回傳:
        bool: 刪除成功返回 True，失敗返回 False
    """
    if not article_id or not isinstance(article_id, int) or article_id <= 0:
        log.warning(f"Invalid article ID provided: {article_id}")
        return False
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {article_tbl}
                WHERE id = ?
            """, (article_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"Successfully deleted article with ID: {article_id}")
                return True
            else:
                log.warning(f"No article found with ID: {article_id}")
                return False
                
    except sqlite3.Error as e:
        log.error(f"Error deleting article with ID {article_id}: {str(e)}")
        return False

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
                FROM {article_tbl}
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
                SELECT * FROM {article_tbl}
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
def delete_article(article_id):
    """
    根據文章 ID 刪除文章
    
    參數:
        article_id (int): 要刪除的文章 ID
        
    回傳:
        bool: 刪除成功返回 True，失敗返回 False
    """
    if not article_id or not isinstance(article_id, int) or article_id <= 0:
        log.warning(f"Invalid article ID provided: {article_id}")
        return False
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {article_tbl}
                WHERE id = ?
            """, (article_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                log.info(f"Successfully deleted article with ID: {article_id}")
                return True
            else:
                log.warning(f"No article found with ID: {article_id}")
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
                log.warning(f"Table '{tbl}' does not exist")
                return False
                
            # Drop table
            cursor.execute(f"DROP TABLE {tbl}")
            conn.commit()
            log.info(f"Successfully dropped table '{tbl}'")

            return True
            
    except sqlite3.Error as e:
        log.error(f"Error dropping table '{tbl}': {str(e)}")
        return False
    
# Initialize the database when this module is imported
init_db()
