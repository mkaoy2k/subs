"""
Publication Management

This page provides functionality for managing newsletter publications.
"""
import streamlit as st
from email_utils import send_newsletter
from admin_ui import init_session_state, show_admin_sidebar
from context_utils import init_context, update_context
import db_utils as dbm

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
st.title("Publication Management")

# Publications
st.subheader("Newsletter for Active Subscribers")

# Publication actions
context = st.session_state.get('app_context', init_context())
lang_list = dbm.get_article_languages()
l10n =st.selectbox("Select Publishing Language", 
                   lang_list,
                   index=0 if not context.get('language') else lang_list.index(context.get('language')))
update_context({'language': l10n})
if st.button(f"Publish Newsletter for {l10n}", type="primary"):
    with st.spinner("Publishing newsletter..."):
        try:
           # 定義 CSS 樣式
           css_style = """
           <style>
               @keyframes blinker {
                   50% { opacity: 0.5; }
               }
               .publish-message {
                   font-size: 24px;
                   font-weight: bold;
                   animation: blinker 1s linear infinite;
                   color: #1f77b4;
               }
           </style>
           """
           # 顯示發布訊息和連結
           ops_svr = context.get('ops_svr')
           st.markdown(css_style, unsafe_allow_html=True)
           st.markdown(f'<div class="publish-message">Confirm to publish, click the link below:</div>', 
                       unsafe_allow_html=True)
           st.markdown(f'<div class="publish-message" style="font-size: 50px;"><a href="{ops_svr}/pub?lang={l10n}">FamilyTreesOps</a></div>', 
                       unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to publish newsletter: {str(e)}")

# Bithday List of the Month
st.subheader("Birthday List of the Month")
st.markdown("🚧 Under Construction: This is the birthday list of the month.")
st.markdown("---")
st.subheader("Quick Navigation")

col1, col2 = st.columns(2)
with col1:
    if st.button("← Back to Admin DBM"):
        st.switch_page("admin_ui.py")
        
with col2:
    if st.button("View Subscribers"):
        st.switch_page("pages/1_usrMgmt.py")
