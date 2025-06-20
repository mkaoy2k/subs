"""
Context Utilities

This module provides utility functions for managing application context and settings.
"""
import importlib.util
import os
from typing import Dict, Any
import streamlit as st
import db_utils as dbm

# ===== Application Settings (Module Level) =====
# These settings can be imported by other modules using context_utils

# General Settings
TIMEZONE = "UTC"
ENABLE_MAINTENANCE = False
SITE_TITLE = "Admin DBM"

# Language Settings
LANGUAGE = dbm.get_article_languages()

# Email Settings
EMAIL_NOTIFICATIONS = True
DEFAULT_EMAIL = "mkaoy2k@gmail.com"

# UI Settings
DARK_MODE = False
ITEMS_PER_PAGE = 20

# Security Settings
PASSWORD_RESET_TIMEOUT = 24  # hours
MAX_LOGIN_ATTEMPTS = 5

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
        'language': LANGUAGE,
        'default_email': DEFAULT_EMAIL,
        'email_notifications': EMAIL_NOTIFICATIONS,
        'dark_mode': DARK_MODE,
        'items_per_page': ITEMS_PER_PAGE,
        'password_reset_timeout': PASSWORD_RESET_TIMEOUT,
        'max_login_attempts': MAX_LOGIN_ATTEMPTS
    }
    
    return default_settings

# 更新 context 的函數
def update_context(new_values: dict):
    if 'app_context' not in st.session_state:
        st.session_state.app_context = init_context()
    st.session_state.app_context.update(new_values)
    
# 範例使用
if __name__ == "__main__":
    update_context({'timezone': 'Asia/Taipei'})
    print("Current context:", st.session_state.app_context)
