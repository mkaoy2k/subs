"""
Publication Management

This page provides functionality for publishing newsletters in
various languages.
"""
import streamlit as st
from subs_ui import show_admin_sidebar
import context_utils as cu
import funcUtils as fu
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
st.header(f"{UI_TEXTS['PUBLICATION']} {UI_TEXTS['MANAGEMENT']}")

st.subheader(f"{UI_TEXTS['NEWSLETTER']}")

context = st.session_state.get('app_context', cu.init_context())
lang_list = dbm.get_article_languages()
l10n =st.selectbox(f"{UI_TEXTS['SELECT']} {UI_TEXTS['LANGUAGE']}", 
                   lang_list,
                   index=0 if not context.get('language') else lang_list.index(context.get('language')))
cu.update_context({'language': l10n})
if st.button(f"{UI_TEXTS['PUBLISH']} {UI_TEXTS['LANGUAGE']}:{l10n}", type="primary"):
    with st.spinner(f"{UI_TEXTS['PUBLISH']} {UI_TEXTS['IN_PROGRESS']} ..."):
        try:
           # Define CSS styles
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
           # Display publication message and link
           ops_svr = context.get('ops_svr')
           
           st.markdown(css_style, unsafe_allow_html=True)
           st.markdown(f'<div class="publish-message">{UI_TEXTS["CONFIRM"]}: {UI_TEXTS["PUBLISH"]} {UI_TEXTS["LANGUAGE"]}:{l10n}, click the link below:</div>', 
                       unsafe_allow_html=True)
           st.markdown(f'<div class="publish-message" style="font-size: 50px;"><a href="{ops_svr}/pub?lang={l10n}&email={st.session_state.user_email}&password={st.session_state.user_pass}" target="_blank">FamilyTreesOps</a></div>', 
                       unsafe_allow_html=True)
        except Exception as e:
            st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['PUBLISH']} {UI_TEXTS['LANGUAGE']}: {l10n}: {str(e)} {UI_TEXTS['FAILED']}")

st.markdown("---")
st.subheader(f"{UI_TEXTS['NAVIGATION']}")

col1, col2 = st.columns(2)
with col1:
    if st.button(f"← {UI_TEXTS['BACK_TO_HOME']}"):
        st.switch_page("subs_ui.py")
        
with col2:
    if st.button(f"{UI_TEXTS['MANAGE']} {UI_TEXTS['SUBSCRIBERS']}"):
        st.switch_page("pages/1_usrMgmt.py")
