"""
資料庫工具模組 (Database Utilities Module)

此模組提供與 SQLite 資料庫互動的相關功能，
包括：
- 資料庫連接管理
- 訂閱者資料的增刪查改 (CRUD)
- 電子郵件驗證令牌處理
- 資料庫初始化與設定

環境變數需求:
- DB_NAME: 資料庫檔案名稱
- TBL_USR: 資料表 User 名稱
- TBL_ARTICLE: 資料表 Article 名稱
- LOGGING: 日誌記錄層級 (DEBUG/INFO/WARNING/ERROR/CRITICAL)

主要功能:
- 管理訂閱者的電子郵件和驗證狀態
- 處理訂閱/取消訂閱流程
- 提供查詢介面取得訂閱者資訊
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
            l10n TEXT NOT NULL DEFAULT 'US',
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
            l10n TEXT NOT NULL DEFAULT 'US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        sql_stmt = f"{cmd} {args}"
        conn.execute(sql_stmt)
        conn.commit()

def add_subscriber(email, token):
    """Add a new subscriber with pending status 
    or update existing one with active status"""
    with get_db_connection() as conn:
        try:
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
    """Unsubscribe an email"""
    with get_db_connection() as conn:
        conn.execute(f'''
        UPDATE {user_tbl} 
        SET is_active = {States['inactive']}, updated_at = CURRENT_TIMESTAMP 
        WHERE email = ?
        ''', (email,))
        conn.commit()
        return conn.total_changes > 0

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

def get_subscribers(state='active'):
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
            SELECT id, email, token, is_active, created_at, updated_at 
            FROM {user_tbl} 
            ORDER BY created_at DESC
        """)
        else:
            cursor = conn.execute(f"""
            SELECT id, email, token, is_active, created_at, updated_at 
            FROM {user_tbl} 
            WHERE is_active = ?
            ORDER BY created_at DESC
        """, (States[state],))
        
        subscribers = [dict(row) for row in cursor.fetchall()]
        
        log.debug(f"Fetched {len(subscribers)} {state} subscribers")
        return subscribers

def get_user(email):
    """
    根據電子郵件查詢單一用戶記錄
    
    此函數用於根據電子郵件地址查詢資料庫中的用戶記錄。
    如果找到對應的用戶，返回包含用戶資訊的字典；
    如果沒有找到，則返回 None。
    
    參數:
        email (str): 要查詢的電子郵件地址
        
    返回:
        dict or None: 包含用戶資訊的字典，若無則返回 None。
                     字典包含以下鍵值：
                     - id: 用戶唯一識別碼
                     - email: 電子郵件地址
                     - token: 驗證令牌
                     - is_active: 帳號狀態 (1/0/-1)
                     - created_at: 建立時間
                     - updated_at: 最後更新時間
    """
    if not email or not isinstance(email, str):
        log.warning("Invalid email provided to get_user")
        return None
        
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(f"""
            SELECT id, email, token, is_active, created_at, updated_at 
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

def delete_user(email):
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
    根據分類取得最新的文章
    
    參數:
        category (str): 文章分類
        limit (int): 取得的文章數量
        
    回傳:
        list of 文章資訊的字典，若無則返回 None。
        字典包含以下鍵值：
        - id: 文章ID
        - title: 文章標題
        - content: 文章內容
        - category: 文章分類
        - author: 作者
        - source: 來源
        - src_url: 來源網址
        - image_url: 圖片網址
        - l10n: 語系
        - created_at: 建立時間
        - updated_at: 更新時間
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
    根據分類取得最近 N 天的文章
    
    參數:
        category (str): 文章分類
        byDays (int): 天數範圍，預設為 7 天
        
    回傳:
        list of 文章資訊的字典，若無則返回 None。
        字典包含以下鍵值：
        - id: 文章ID
        - title: 文章標題
        - content: 文章內容
        - category: 文章分類
        - author: 作者
        - source: 來源
        - src_url: 來源網址
        - image_url: 圖片網址
        - l10n: 語系
        - created_at: 建立時間
        - updated_at: 更新時間
    """
    if not category:
        log.warning("No category provided to get_articles_byDays")
        return None
        
    # 計算 N 天前的日期
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
    取得所有不重複的文章分類
    
    回傳:
        list: 包含所有不重複分類名稱的列表，按字母順序排序
        
    範例:
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
            
            # 將結果轉換為簡單的列表
            categories = [row[0] for row in cursor.fetchall()]
            log.debug(f"Found {len(categories)} unique categories")
            return categories
            
    except sqlite3.Error as e:
        log.error(f"Error fetching article categories: {str(e)}")
        return []

def get_article_byId(article_id):
    """
    根據文章 ID 取得單一文章
    
    參數:
        article_id (int): 要取得的文章 ID
        
    回傳:
        dict: 包含文章資訊的字典，若無則返回 None
        字典包含以下鍵值：
        - id: 文章ID
        - title: 文章標題
        - content: 文章內容
        - category: 文章分類
        - author: 作者
        - source: 來源
        - src_url: 來源網址
        - image_url: 圖片網址
        - l10n: 語系
        - created_at: 建立時間
        - updated_at: 更新時間
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

# Initialize the database when this module is imported
init_db()
