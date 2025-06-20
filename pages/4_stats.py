"""
Admin Statistics

This is the main dashboard page that appears after successful login.
It provides an overview and quick access to various admin functions.
"""
import streamlit as st
from admin_ui import show_admin_sidebar, init_session_state

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
st.title("Statistics")
st.markdown("---")

# Dashboard content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Quick Actions")
    if st.button("User Management"):
        st.switch_page("pages/1_usrMgmt.py")
    if st.button("Article Management"):
        st.switch_page("pages/2_artMgmt.py")

with col2:
    st.subheader("Settings")
    if st.button("Settings"):
        st.switch_page("pages/5_settings.py")
    if st.button("Statistics"):
        st.switch_page("pages/4_stats.py")

# Add some metrics or statistics
st.markdown("---")
st.subheader("System Overview")

# Example metrics
try:
    import db_utils as dbm
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
        
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", user_count)
    with col2:
        st.metric("Admin Users", admin_count)
    with col3:
        st.metric("Database Tables", table_count)
        
except Exception as e:
    st.error(f"Error loading system metrics: {str(e)}")
