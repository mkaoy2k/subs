"""
Article Management

This page provides functionality for managing articles in the system.
"""
import streamlit as st
import pandas as pd
from admin_ui import show_admin_sidebar, init_session_state
import db_utils as dbm

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

# Initialize session state
init_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    st.switch_page("admin_ui.py")
    
# Show admin sidebar
show_admin_sidebar()

# Main content
st.title("Article Table Management")

# Add article management UI components here
with st.container():
    try:
        st.markdown("---")
        st.subheader("Query Articles")
        cats = dbm.get_article_categories()
        if not cats:
            st.warning("No categories found. Please add categories first.")
            st.stop()
            
        cat = st.selectbox("Category:", cats)
        
        col1, col2 = st.columns(2)
        with col1:
            # Add numeric input box for article limit
            limit = st.number_input(
                "Number of articles to fetch:",
                min_value=1,
                max_value=100,
                value=10,
                step=1,
                format="%d",
                help="Enter the number of articles you want to retrieve (1-100)"
            )
            
        with col2:
            # Query articles by last number of days
            by_days = st.number_input(
                "Last number of days from now:",
                min_value=1,
                max_value=365,
                value=7,
                step=1,
                format="%d",
                help="Enter the number of days by which you want to query articles"
            )
        
        # Initialize articles variable
        articles = []
        
        # Query buttons
        btn11, btn12 = st.columns(2)
        
        with btn11:
            if st.button("Query by limit"):
                articles = dbm.get_articles(cat, limit=limit)
                
        with btn12:
            if st.button("Query by days"):
                articles = dbm.get_articles_byDays(cat, byDays=by_days)
                
        info1, info2 = st.columns([15,1])
        # Display results if articles were found
        if articles:
            df = pd.DataFrame(articles)
            if not df.empty:
                df = format_timestamps(df)
                with info1:
                    st.dataframe(df)
                    st.success(f"Retrieved {len(articles)} articles")
            else:
                with info1:
                    st.info("No articles found")
        else:
            with info1:
                st.info("Click a query button to load articles")
        
        # --- Manage a specific article ---
        st.markdown("---")
        st.subheader("Manage Articles")
        
        article_id = st.number_input(
            "Article ID:",
            min_value=1,
            step=1,
            format="%d",
            help="Enter the article ID you want to retrieve (must be a positive integer)"
        )
        article = dbm.get_article_byId(article_id)
        
        btn21, btn22 = st.columns(2)
        if article:
            with btn21:
                if st.button("Query"):
                    info21, info22 = st.columns([5,5])
                    for i, (key, value) in enumerate(article.items()):
                        # Convert timestamp to local time if needed
                        if key in ['created_at', 'updated_at'] and value is not None:
                            value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                        if i % 2 == 0:
                            with info21:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        else:
                            with info22:
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    st.success(f"Retrieved article with ID: {article_id}")
            with btn22:
                if st.button("Delete"):
                    if dbm.delete_article(article_id):
                        st.success(f"Deleted article Id: {article_id}")
                    else:
                        st.error(f"Failed to delete article Id: {article_id}")        
        else:
            st.info("Enter a valid article ID")        
        
        st.markdown("""---""")
        st.subheader("Review Pending Articles")

        # Review pending articles from id = 1
        result = dbm.get_next_article(1)
        if result is None:
            st.info("No more articles to review")
            st.stop()
        review_id, article = result
        
        info31, info32 = st.columns([15,1])
        for i, (key, value) in enumerate(article.items()):
            # 轉換時間戳記為本地時間
            if key in ['created_at', 'updated_at'] and value is not None:
                value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
            with info31:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        with info31:
            st.success(f"Review article with ID: {review_id}")
        
        btn31, btn32 = st.columns(2)

        with btn31:
            if st.button(f"Approve Id: {review_id}"):
                if dbm.approve_article(review_id, dbm.Article_State['approved']):
                    st.success(f"Approved article with ID: {review_id}")
                else:
                    st.error(f"Failed to approve article with ID {review_id}")
        
        with btn32:
            if st.button(f"Reject Id: {review_id}"):
                if dbm.approve_article(review_id, dbm.Article_State['rejected']):
                    st.success(f"Rejected article with ID: {review_id}")
                else:
                        st.error(f"Failed to reject article with ID {review_id}")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)  # This will show the full traceback for debugging
