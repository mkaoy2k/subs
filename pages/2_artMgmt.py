"""
Article Management

This page provides functionality for managing articles in the system.
"""
import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from subs_ui import UI_TEXTS, show_admin_sidebar
import db_utils as dbm
import email_utils as eu
import context_utils as cu
import funcUtils as fu
import logging

# Configure logging
log = logging.getLogger(__name__)

def run_article_editor(db_path, table_name):
    """Run the article editor in a separate process.
    
    Args:
        db_path (str): Path to the database
        table_name (str): Name of the table to edit
    """
    try:
        # Get the path to the current Python interpreter
        python_exec = sys.executable
        # Get the path to the current script
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ops_artBatch.py')
        
        # Start the process
        subprocess.Popen([
            python_exec, 
            script_path,
            '--db', db_path,
            '--table', table_name
        ], 
        # These arguments prevent the subprocess from inheriting stdin/stdout
        # which would prevent the Streamlit app from continuing
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True)
        
        return True
    except Exception as e:
        st.error(f"️❌ {fu.get_function_name()}: Failed to start article editor: {str(e)}")
        return False

def format_timestamps(df):
    """
    Format timestamp columns in the dataframe.
    Handles None values and malformed timestamps gracefully.
    
    Args:
        df (pd.DataFrame): Input dataframe with timestamp columns
        
    Returns:
        pd.DataFrame: DataFrame with formatted timestamps
    """
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            try:
                # First convert to datetime, handling errors
                df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
                
                # Convert timezone and format, handling NaT (Not a Time) values
                df[col] = df[col].apply(
                    lambda x: x.tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                    if pd.notna(x) else None
                )
            except Exception as e:
                st.warning(f"⚠️ {fu.get_function_name()}: Could not format {col} column: {str(e)}")
                # If any error occurs, keep the original value
                continue
    return df

def display_article(article, info):
    """
    Display article information in a formatted way, 
    distributed across two columns.
    
    Args:
        article (dict): Article information to display
        info: Streamlit container for the article display
    """
    # Split items into two columns
    items = list(article.items())
    half = (len(items) + 1) // 2  # Ceiling division to handle odd counts
    with info:
        col1, col2 = st.columns([5, 5])
    
        # First half items in left column
        for key, value in items[:half]:
            if key in ['created_at', 'updated_at'] and value is not None:
                value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
            with col1:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
        # Second half items in right column
        for key, value in items[half:]:
            if key in ['created_at', 'updated_at'] and value is not None:
                value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
            with col2:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

def main():
    global UI_TEXTS
    # Check authentication
    if not st.session_state.get('authenticated', False):
        st.switch_page("subs_ui.py")
    
    # Show admin sidebar
    with st.sidebar:
        show_admin_sidebar()
        st.header(f"{UI_TEXTS['ARTICLE']} {UI_TEXTS['MANAGEMENT']}")
        if st.button(f"{UI_TEXTS['OPEN']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['EDITOR']}"):
            if run_article_editor(dbm.dbn, dbm.db_tables['article']):
                st.success(f"✅ Article editor launched in a separate window")
            else:
                st.error(f"️❌ {fu.get_function_name()}: Failed to launch article editor")

    # Show admin main content
    st.header(f"{UI_TEXTS['ARTICLE']} {UI_TEXTS['TABLE']} {UI_TEXTS['MANAGEMENT']}")
    context = st.session_state.get('app_context', cu.init_context())
    ops_svr = context.get('ops_svr')

    # Initialize session state variables
    if 'article_id' not in st.session_state:
        st.session_state.article_id = 1
    if 'publisher' not in st.session_state:
        # Get email credentials from context
        email_user = context.get('email_user')
        email_pass = context.get('email_pass')
        
        # Log the email configuration (without password)
        if email_user:
            log.info(f"️{fu.get_function_name()}: Initializing email publisher with user: {email_user}")
        else:
            log.error(f"️{fu.get_function_name()}: email_user is not set in the context")
        
        # Initialize the email publisher
        st.session_state.publisher = eu.EmailPublisher(email_user, email_pass)

    # Add article management UI components here
    with st.container():
        try:
            # --- Query articles --- from here
            st.subheader(f"{UI_TEXTS['QUERY']} {UI_TEXTS['ARTICLES']}")
            cats = list(dbm.Article_Categories.keys())
            if not cats:
                st.warning(f"️⚠️ {fu.get_function_name()}: No categories found. Please add categories first.")
                st.stop()
                
            # Find index of 'news' category, default to 0 if not found
            news_index = list(dbm.Article_Categories.keys()).index('news') if 'news' in dbm.Article_Categories else 0
            cat_key = st.selectbox(
                f"{UI_TEXTS['CATEGORY']}:",
                options=cats,
                index=news_index
            )
            
            col1, col2 = st.columns([5,5])
            with col1:
                # Add numeric input box for article limit
                limit = st.number_input(
                    f"{UI_TEXTS['NUMBER_OF_APPROVED_ARTICLES']}",
                    min_value=1,
                    max_value=10,
                    value=10,
                    step=1,
                    format="%d",
                    help=f"{UI_TEXTS['ENTER']} {UI_TEXTS['NUMBER_OF_APPROVED_ARTICLES']}"
                )
                
            with col2:
                # Query articles by last number of days
                by_days = st.number_input(
                    f"{UI_TEXTS['NUMBER_OF_DAYS']}",
                    min_value=1,
                    max_value=365,
                    value=7,
                    step=1,
                    format="%d",
                    help=f"{UI_TEXTS['ENTER']} {UI_TEXTS['NUMBER_OF_DAYS']}"
                )
            
            # Initialize articles variable
            articles = []
            
            # Query buttons
            btn11, btn12 = st.columns([5,5])
            
            with btn11:
                if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['BY_LIMIT']}"):
                    articles = dbm.get_articles(dbm.Article_Categories[cat_key], limit=limit)
                    
            with btn12:
                if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['BY_DAYS']}"):
                    articles = dbm.get_articles_byDays(dbm.Article_Categories[cat_key], byDays=by_days)
                    
            info1, info2 = st.columns([15,1])
            # Display results if articles were found
            if articles:
                df = pd.DataFrame(articles)
                if not df.empty:
                    df = format_timestamps(df)
                    with info1:
                        st.dataframe(df)
                        st.success(f"✅ {UI_TEXTS['RETRIEVED']} {len(articles)} {UI_TEXTS['ARTICLES']}")
            
            col1, col2 = st.columns([5,5])
            with col1:
                cursor_id = st.number_input(
                    f"{UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}:",
                    min_value=1,
                    value=st.session_state.article_id,
                    step=1,
                    format="%d",
                    help=f"{UI_TEXTS['ENTER']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}"
                    )
            with col2:
                # Get Article_State keys as options
                article_state_options = list(dbm.Article_State.keys())
                article_state = st.selectbox(
                    f"{UI_TEXTS['ARTICLE_STATE']}:",
                    options=article_state_options,
                    index=len(article_state_options) - 1
                    )
            
            btn21, btn22 = st.columns([5, 5])
            with btn21:
                if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['BY_ID']}"):
                    article = dbm.get_article_byId(cursor_id)
                    if article:
                        display_article(article, info1)
                        st.session_state.article_id = article['id']
                        st.success(f"✅ {UI_TEXTS['RETRIEVED']} {UI_TEXTS['ARTICLE']}: {article['id']}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}: {cursor_id} {UI_TEXTS['NOT_FOUND']}")
            with btn22:
                if st.button(f"{UI_TEXTS['QUERY']} {UI_TEXTS['NEXT']} {UI_TEXTS['FEEDBACK']} {UI_TEXTS['BY_STATE']}"):
                    result = dbm.get_next_article(
                        cursor_id, dbm.Article_Categories[cat_key], 
                        is_censored=dbm.Article_State[article_state]
                        )
                    if result is not None:
                        article_id, article = result
                        display_article(article, info1)
                        st.session_state.article_id = article_id
                        st.success(f"✅ {UI_TEXTS['RETRIEVED']} '{cat_key}':'{article_state}' {UI_TEXTS['NEXT']} {UI_TEXTS['ARTICLE']}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: '{cat_key}':'{article_state}' {UI_TEXTS['ARTICLE']} {UI_TEXTS['NOT_FOUND']}")
            # Show delete button
            with st.expander(f"{UI_TEXTS['DANGER_ZONE']}", expanded=False):
                st.warning(f"⚠️ {UI_TEXTS['CANNOT_BE_UNDONE']}")
                if st.button(f"{UI_TEXTS['DELETE']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}: {cursor_id}"):
                    if dbm.delete_article(cursor_id):
                        st.success(f"✅ {UI_TEXTS['DELETED']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}: {cursor_id}")
                    else:
                        st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['DELETE']} {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}: {cursor_id} {UI_TEXTS['FAILED']}")
            
            # --- Review pending feedback --- from here
            st.subheader(f"{UI_TEXTS['REVIEW']} {UI_TEXTS['FEEDBACK']}")
            info3, info4 = st.columns([15,1])
            result = dbm.get_next_article(1, 
                            dbm.Article_Categories['feedback'], 
                            is_censored=dbm.Article_State['pending'])
            if result is None:
                st.info(f"ℹ️ {UI_TEXTS['NO_MORE']} {UI_TEXTS['PENDING']} {UI_TEXTS['FEEDBACKS']}")
            else:
                review_id, article = result
                article['category'] = dbm.Article_Categories[cat_key]
                display_article(article, info3)
            
                btn31, btn32 = st.columns([5, 5])

                with btn31:
                    if st.button(f"{UI_TEXTS['APPROVE']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['CATEGORY']}: {dbm.Article_Categories[cat_key]}"):
                        if dbm.review_article(review_id, 
                                dbm.Article_State['approved'],
                                category=dbm.Article_Categories[cat_key]):
                            # Send approval notification email to subscriber
                            subject = f"{UI_TEXTS['TICKET']}: {review_id} {UI_TEXTS['APPROVED']}"
                            html = r"""
                            <style>
                                .publish-message {
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: #1f77b4;
                                }
                            </style>""" + f"""
                            <div class="publish-message">
                            <p>{UI_TEXTS['ARTICLE']} {UI_TEXTS['APPROVED']}:</p>
                            <p><strong>{UI_TEXTS['TITLE']}:</strong> {article.get('title', '')}</p>
                            <p><strong>{UI_TEXTS['CATEGORY']}:</strong> {dbm.Article_Categories[cat_key]}</p>
                            <p><strong>{UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}:</strong> {review_id}</p>
                            <p>{UI_TEXTS['THANK_YOU']}!</p>
                            </div>
                            <div class="publish-message">
                            Visit us at: <a href="{ops_svr}">FamilyTreesOps</a>
                            </div>
                            """
                            # Get subscriber email if available
                            user_email = None
                            if article.get('user_id'):
                                user_email = dbm.get_user_email(article['user_id'])
                                
                                # Send to subscriber if available, otherwise to admin
                                to_emails = [user_email] if user_email else [st.session_state.get('admin_email')]
                                
                                if st.session_state.publisher.publish_email(
                                    subject,
                                    f"ref: {UI_TEXTS['TICKET']} {UI_TEXTS['ID']}: {review_id}",
                                    html,
                                    to_emails
                                    ):
                                    msg = f"✅ {UI_TEXTS['ARTICLE']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['CATEGORY']}: {cat}"
                                    log.info(msg)
                                    st.success(msg)
                                else:
                                    msg = f"️❌ {fu.get_function_name()}: {to_emails} {UI_TEXTS['EMAIL_SENT_FAILED']}. {UI_TEXTS['TICKET']} {UI_TEXTS['ID']}: {review_id}"
                                    log.error(msg)
                                    st.error(msg)
                            else:
                                msg = f"️❌ {fu.get_function_name()}: {UI_TEXTS['USER']} {UI_TEXTS['EMAIL']} {UI_TEXTS['NOT_FOUND']}. {UI_TEXTS['TICKET']} {UI_TEXTS['ID']}: {review_id}"
                                log.error(msg)
                                st.error(msg)
                        else:
                            st.error(f"❌ {UI_TEXTS['APPROVE']} {UI_TEXTS['FEEDBACK']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['CATEGORY']}: {cat} {UI_TEXTS['FAILED']}")
            
                with btn32:
                    if st.button(f"{UI_TEXTS['REJECT']} {UI_TEXTS['FEEDBACK']} {UI_TEXTS['ID']}: {review_id}"):
                        if dbm.review_article(review_id, dbm.Article_State['rejected'],
                                category=dbm.Article_Categories[cat_key]):
                            st.success(f"✅ {UI_TEXTS['REJECT']} {UI_TEXTS['FEEDBACK']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['CATEGORY']}: {cat}")
                        else:
                            st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['REJECT']} {UI_TEXTS['FEEDBACK']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['CATEGORY']}: {cat} {UI_TEXTS['FAILED']}")
            
            # --- Review Pending Contact --- from here
            st.subheader(f"{UI_TEXTS['REVIEW']} {UI_TEXTS['CONTACT']}")
            info5, info6 = st.columns([15,1])
            result = dbm.get_next_article(1,
                    dbm.Article_Categories['contact'],
                    is_censored=dbm.Article_State['pending'])
            if result is None:
                st.info(f"ℹ️ {UI_TEXTS['NO_MORE']} {UI_TEXTS['PENDING']} {UI_TEXTS['CONTACTS']}")
                st.stop()
            else:
                review_id, article = result
                display_article(article, info5)
            
                btn41, btn42 = st.columns([5, 5])

                with btn41:
                    if st.button(f"Completed ID: {review_id}"):
                        if dbm.review_article(review_id, 
                                dbm.Article_State['action_taken']):
                            # Send action taken notification email to subscriber
                            subject = f"{UI_TEXTS['TICKET']} {review_id} {UI_TEXTS['COMPLETED']}"
                            html = r"""
                            <style>
                                .publish-message {
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: #1f77b4;
                                }
                            </style>""" + f"""
                            <div class="publish-message">
                            <p>{UI_TEXTS['CONTACT_REQUEST_COMPLETED']}</p>
                            <p><strong>{UI_TEXTS['TITLE']}:</strong> {article.get('title', '')}</p>
                            <p><strong>{UI_TEXTS['CONTENT']}:</strong> {article.get('content', '')}</p>
                            <p><strong>{UI_TEXTS['TICKET']} {UI_TEXTS['ID']}:</strong> {review_id}</p>
                            <p>{UI_TEXTS['THANK_YOU']}!</p>
                            </div>
                            <div class="publish-message">
                            Visit us at: <a href="{ops_svr}">FamilyTreesOps</a>
                            </div>
                            """
                            # Get user email if available
                            user_email = None
                            if article.get('user_id'):
                                user_email = dbm.get_user_email(article['user_id'])
                                
                                # Send to user if available, otherwise to admin
                                to_emails = [user_email] if user_email else [st.session_state.get('admin_email')]
                                
                                if st.session_state.publisher.publish_email(
                                    subject,
                                    f"ref: Ticket ID:{review_id}",
                                    html,
                                    to_emails
                                ):
                                    msg = f"✅ {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['COMPLETED']}"
                                    log.info(msg)
                                    st.success(msg)
                                else:
                                    msg = f"❌ {fu.get_function_name()}: {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['FAILED']}"
                                    log.error(msg)
                                    st.error(msg)
                            else:
                                msg = f"❌ {fu.get_function_name()}: {UI_TEXTS['USER']} {UI_TEXTS['EMAIL']} {UI_TEXTS['NOT_FOUND']}. {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id}"
                                log.error(msg)
                                st.error(msg)
                        else:
                            msg = f"❌ {fu.get_function_name()}: {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['FAILED']}"
                            log.error(msg)
                            st.error(msg)
            
                with btn42:
                    if st.button(f"{UI_TEXTS['IGNORE']} ID: {review_id}"):
                        if dbm.review_article(review_id, dbm.Article_State['ignored']):
                            st.success(f"✅ {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['IGNORED']}")
                        else:
                            st.error(f"❌ {fu.get_function_name()}: {UI_TEXTS['IGNORE']} {UI_TEXTS['CONTACT']} {UI_TEXTS['ID']}: {review_id} {UI_TEXTS['FAILED']}")
        
        except Exception as e:
            st.error(f"️❌ {fu.get_function_name()}: {UI_TEXTS['ARTICLE']} {UI_TEXTS['MANAGEMENT']} {UI_TEXTS['FAILED']}: {str(e)}")
            st.exception(e)  # This will show the full traceback for debugging

# Initialize session state
cu.init_session_state()
UI_TEXTS = st.session_state.ui_context[st.session_state.app_context.get('language', "US")]

if __name__ == "__main__":
    main()
