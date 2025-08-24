"""
Admin Statistics

This is the main dashboard page that appears after successful login.
It provides an overview and quick access to various admin functions.
"""
import streamlit as st
from subs_ui import show_admin_sidebar
import context_utils as cu
import db_utils as dbm

# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("subs_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
st.title(UI_TEXTS["STATISTICS"])
st.markdown("---")

# Dashboard content
col1, col2 = st.columns(2)

with col1:
    st.subheader(UI_TEXTS["NAVIGATION"])
    if st.button(f"{UI_TEXTS['OPEN']} {UI_TEXTS['USER']} {UI_TEXTS['MANAGEMENT']} {UI_TEXTS['PAGE']}"):
        st.switch_page("pages/1_usrMgmt.py")
    if st.button(f"{UI_TEXTS['OPEN']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['MANAGEMENT']} {UI_TEXTS['PAGE']}"):
        st.switch_page("pages/2_artMgmt.py")
    if st.button(f"{UI_TEXTS['OPEN']} {UI_TEXTS['PUBLICATION']} {UI_TEXTS['MANAGEMENT']} {UI_TEXTS['PAGE']}"):
        st.switch_page("pages/3_pubMgmt.py")
    
with col2:
    st.subheader(UI_TEXTS["SETTINGS"])
    if st.button(f"{UI_TEXTS['OPEN']} {UI_TEXTS['SETTINGS']} {UI_TEXTS['PAGE']}"):
        st.switch_page("pages/5_settings.py")

# Add some metrics or statistics
st.markdown("---")
st.subheader(f"{UI_TEXTS['DATABASE']} {UI_TEXTS['OVERVIEW']}")

# Example metrics
try:
    with dbm.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        # Get admin count
        cursor.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1")
        admin_count = cursor.fetchone()[0]
        
        # Get table count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        table_count = cursor.fetchone()[0]
        
        # Get article count
        cursor.execute("SELECT COUNT(*) FROM article")
        article_count = cursor.fetchone()[0]
        
        # Get Category count
        category_count = len(dbm.get_article_categories())
        
        # Get subscription count
        subscription_count = len(dbm.get_subscribers())
        
    # Display metrics
    col1, col2  = st.columns(2)
    with col2:
        st.metric(f"{UI_TEXTS['TOTAL']} {UI_TEXTS['USERS']}", user_count)
        st.metric(f"{UI_TEXTS['TOTAL']} {UI_TEXTS['ADMIN']} {UI_TEXTS['USERS']}", admin_count)
        st.metric(f"{UI_TEXTS['TOTAL']} {UI_TEXTS['SUBSCRIBERS']}", subscription_count)
    with col1:
        st.metric(f"{UI_TEXTS['DATABASE']} {UI_TEXTS['TABLES']}", table_count)
        st.metric(f"{UI_TEXTS['TOTAL']} {UI_TEXTS['ARTICLES']}", article_count)
        st.metric(f"{UI_TEXTS['TOTAL']} {UI_TEXTS['CATEGORIES']}", category_count)
        
except Exception as e:
    st.error(f"️❌ {fu.get_function_name()}: Error loading system metrics: {str(e)}")
