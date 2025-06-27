"""
Article Management

This page provides functionality for managing articles in the system.
"""
import streamlit as st
import pandas as pd
import subprocess
import sys
import os
from admin_ui import show_admin_sidebar, init_session_state
import db_utils as dbm
from ops_artBatch import show_window

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
        st.error(f"Failed to start article editor: {str(e)}")
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
                st.warning(f"Warning: Could not format {col} column: {str(e)}")
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

# Initialize session state
init_session_state()

# Initialize session state variables
if 'article_id' not in st.session_state:
    st.session_state.article_id = 1

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
with st.sidebar:
    show_admin_sidebar()
    
    st.divider()
    st.subheader("Article Editor")
    if st.button("Open Article Editor"):
        if run_article_editor(dbm.dbn, dbm.db_tables['article']):
            st.success("Article editor launched in a separate window")
        else:
            st.error("Failed to launch article editor")

# Main content
st.title("Article Table Management")

# Add article management UI components here
with st.container():
    try:
        # --- Query articles --- from here
        st.subheader("Query Articles")
        cats = dbm.get_article_categories()
        if not cats:
            st.warning("No categories found. Please add categories first.")
            st.stop()
            
        cat = st.selectbox("Category:", cats)
        
        col1, col2 = st.columns([5,5])
        with col1:
            # Add numeric input box for article limit
            limit = st.number_input(
                "Number of CENSORED articles to fetch:",
                min_value=1,
                max_value=10,
                value=10,
                step=1,
                format="%d",
                help="Enter the number of censored articles you want to retrieve (1-10)"
            )
            
        with col2:
            # Query articles by last number of days
            by_days = st.number_input(
                "CENSORED articles that are older than number of days from today:",
                min_value=1,
                max_value=365,
                value=7,
                step=1,
                format="%d",
                help="Enter the number of days by which you want to query censored articles"
            )
        
        # Initialize articles variable
        articles = []
        
        # Query buttons
        btn11, btn12 = st.columns([5,5])
        
        with btn11:
            if st.button("Query by limit"):
                articles = dbm.get_articles(cat, limit=limit)
                
        with btn12:
            if st.button("Query by days"):
                articles = dbm.get_articles_byDays(cat, by_days=by_days)
                
        info1, info2 = st.columns([15,1])
        # Display results if articles were found
        if articles:
            df = pd.DataFrame(articles)
            if not df.empty:
                df = format_timestamps(df)
                with info1:
                    st.dataframe(df)
                    st.success(f"Retrieved {len(articles)} articles")
        
        col1, col2 = st.columns([5,5])
        with col1:
            cursor_id = st.number_input(
                "Article ID to Query:",
                min_value=1,
                value=st.session_state.article_id,
                step=1,
                format="%d",
                help="Enter the article ID you want to retrieve (must be a positive integer)"
                )
        with col2:
            # Get Article_State keys as options
            article_state_options = list(dbm.Article_State.keys())
            article_state = st.selectbox(
                "Article State:",
                options=article_state_options,
                index=len(article_state_options) - 1
                )
        
        btn21, btn22 = st.columns([5, 5])
        with btn21:
            if st.button("Query by Id"):
                article = dbm.get_article_byId(cursor_id)
                if article:
                    display_article(article, info1)
                    st.session_state.article_id = article['id']
                    st.success(f"Retrieved article with ID: {article['id']}")
                else:
                    st.error(f"Article with ID {cursor_id} not found")
        with btn22:
            if st.button("Query Next Feedback by State"):
                result = dbm.get_next_article(
                    cursor_id, dbm.Article_Categories['feedback'], 
                    is_censored=dbm.Article_State[article_state]
                    )
                if result is not None:
                    article_id, article = result
                    display_article(article, info1)
                    st.session_state.article_id = article_id
                    st.success(f"Retrieved '{article_state}' feedback with ID: {article_id}")
                else:
                    st.error(f"No '{article_state}' feedback found with ID: {cursor_id}")
        # Show delete button
        with st.expander("Danger Zone", expanded=False):
            st.warning("⚠️ This action cannot be undone!")
            if st.button(f"Delete article Id: {cursor_id}"):
                if dbm.delete_article(cursor_id):
                    st.success(f"✅ Deleted article Id: {cursor_id}")
                else:
                    st.error(f"❌ Failed to delete article Id: {cursor_id}")
        
        # --- Review pending feedback --- from here
        st.markdown("""---""")
        st.subheader("Review Pending Feedback")
        info3, info4 = st.columns([15,1])
        result = dbm.get_next_article(1, 
                        dbm.Article_Categories['feedback'], 
                        is_censored=dbm.Article_State['pending'])
        if result is None:
            st.info("No more articles to review")
        else:
            review_id, article = result
            display_article(article, info3)
        
            btn31, btn32 = st.columns([5, 5])

            with btn31:
                if st.button(f"Approve Id: {review_id}"):
                    if dbm.review_article(review_id, dbm.Article_State['approved']):
                        st.success(f"✅ Approved feedback with ID: {review_id}")
                    else:
                        st.error(f"❌ Failed to approve feedback with ID {review_id}")
        
            with btn32:
                if st.button(f"Reject Id: {review_id}"):
                    if dbm.review_article(review_id, dbm.Article_State['rejected']):
                        st.success(f"✅ Rejected feedback with ID: {review_id}")
                    else:
                        st.error(f"❌ Failed to reject feedback with ID {review_id}")
        
        # --- Review Pending Contact --- from here
        st.markdown("""---""")
        st.subheader("Review Pending Contact")
        info5, info6 = st.columns([15,1])
        result = dbm.get_next_article(1,
                        dbm.Article_Categories['contact'],
                        is_censored=dbm.Article_State['pending'])
        if result is None:
            st.info("No more contacts to review")
            st.stop()
        else:
            review_id, article = result
            display_article(article, info5)
        
            btn41, btn42 = st.columns([5, 5])

            with btn41:
                if st.button(f"Approve Id: {review_id}"):
                    if dbm.review_article(review_id, dbm.Article_State['approved']):
                        st.success(f"✅ Approved contact with ID: {review_id}")
                    else:
                        st.error(f"❌ Failed to approve contact with ID {review_id}")
        
            with btn42:
                if st.button(f"Reject Id: {review_id}"):
                    if dbm.review_article(review_id, dbm.Article_State['rejected']):
                        st.success(f"✅ Rejected contact with ID: {review_id}")
                    else:
                        st.error(f"❌ Failed to reject contact with ID {review_id}")
     
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)  # This will show the full traceback for debugging
