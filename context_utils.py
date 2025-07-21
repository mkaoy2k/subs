"""
Context Utilities

This module provides utility functions for managing application context and settings.
"""
import importlib.util
import os
from typing import Dict, Any
import streamlit as st
import db_utils as dbm
from dotenv import load_dotenv
load_dotenv()
# ===== Application Settings (Module Level) =====
# These settings can be imported by other modules using context_utils

# General Settings
TIMEZONE = os.getenv("TIMEZONE", "UTC")
ENABLE_MAINTENANCE = False
SITE_TITLE = "Admin DBM"
RELEASE = os.getenv("RELEASE", "")

# Language Settings
language_list = dbm.get_article_languages()
LANGUAGES = language_list
LANGUAGE = os.getenv("L10N", "US")

# Email Settings
EMAIL_SUBSCRIPTION = True
MAIL_USER = os.getenv("MAIL_USERNAME", "")
MAIL_PASS = os.getenv("MAIL_PASSWORD", "")

# UI Settings
DARK_MODE = False
ITEMS_PER_PAGE = 20

# Security Settings
PASSWORD_RESET_TIMEOUT = 24  # hours
MAX_LOGIN_ATTEMPTS = 5

# Server Settings
OPS_SVR_PORT = os.getenv("OPS_SVR_PORT", "5566")
OPS_SVR = os.getenv("OPS_SVR", "http://localhost").rstrip('/')

# File System Settings
FILE_SYSTEM_SETTINGS = {
    'dir_path': os.getenv("FSS_DIR_PATH", "./data"),
    'file_name': os.getenv("FSS_FILE_NAME", "users"),
    'file_type': os.getenv("FSS_FILE_TYPE", "CSV")
}
# ===== End of Module Settings =====

def init_context() -> Dict[str, Any]:
    """
    初始化並返回包含設定的全局字典
    
    Returns:
        Dict[str, Any]: 包含設定的字典
    """
    # 預設設定
    default_settings = {
        'timezone': TIMEZONE,
        'enable_maintenance': ENABLE_MAINTENANCE,
        'site_title': SITE_TITLE,
        'release': RELEASE,
        'languages': LANGUAGES,
        'language': LANGUAGE,
        'email_user': MAIL_USER,
        'email_pass': MAIL_PASS,
        'admin_email': os.getenv("DB_ADMIN", ""),
        'email_subscription': EMAIL_SUBSCRIPTION,
        'dark_mode': DARK_MODE,
        'items_per_page': ITEMS_PER_PAGE,
        'password_reset_timeout': PASSWORD_RESET_TIMEOUT,
        'max_login_attempts': MAX_LOGIN_ATTEMPTS,
        'ops_svr': OPS_SVR,
        'fss': FILE_SYSTEM_SETTINGS
    }
    
    return default_settings

# 更新 context 的函數
def update_context(new_values: dict):
    if 'app_context' not in st.session_state:
        st.session_state.app_context = init_context()
    st.session_state.app_context.update(new_values)
    
# Helper function to get full file path with extension
def get_file_path():
    """Generate full file path with correct extension based on selected file type."""
    context = st.session_state.get('app_context', init_context())
    extension = context.get('fss', {}).get('file_type', '').lower()
    dir_path = context.get('fss', {}).get('dir_path', '')
    file_name = context.get('fss', {}).get('file_name', '')
    if not file_name or not extension:
        return "No file path configured"
    return f"{os.path.join(dir_path, file_name)}.{extension}"
    
# 範例使用
if __name__ == "__main__":
    update_context({'timezone': 'Asia/Taipei'})
    print("Current context:", st.session_state.app_context)
    print("File path:", get_file_path())
