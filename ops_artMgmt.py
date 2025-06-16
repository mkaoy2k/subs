"""
Article Table Management Tool

This module provides a web interface for managing article data, including:
- Query article lists (active/pending/inactive)
- Query specific articles by article ID
- Delete articles
- Drop article tables

Environment Variables Required:
- Uses database connection settings defined in the db_utils module

Usage:
    uv run streamlit run ops_article_purge.py
"""

import streamlit as st
import pandas as pd  # pip install pandas
import db_utils as dbm

def format_timestamps(df):
    """Convert UTC timestamps to Pacific Time (with DST) and format"""
    for col in ['created_at', 'updated_at']:
        if col in df.columns:
            # Parse as UTC and convert to Pacific Time (handles DST automatically)
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

st.title("Purge Article Table")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    """
    )
cats = dbm.get_article_categories()
cat = st.selectbox("Category:", cats)

col1, col2 = st.columns(2)
with col1:
    # Add numeric input box, default value is 10, min is 1, max is 100
    limit = st.number_input(
        "Number of articles to fetch:",
        min_value=1,
        step=1,
        format="%d",
        help="Enter the number of articles you want to retrieve (1-100)"
    )
with col2:
    # query articles by last number of days
    byDays = st.number_input(
        "Last number of days from now:",
        min_value=1,
        step=1,
        format="%d",
        help="Enter the number of days by which you want to query articles"
    )
df = pd.DataFrame()
btn1, btn2 = st.columns([5,5])

with btn1:
    if st.button("Query by limit"):
        articles = dbm.get_articles(cat, limit=limit)  # Use user-specified quantity
        if articles:
            df = pd.DataFrame(articles, columns=articles[0].keys())
            df = format_timestamps(df)
            st.dataframe(df)
            st.success(f"Retrieved {len(articles)} articles")
        else:
            st.info("No articles found")    

with btn2:
    if st.button("Query by days"):
        articles = dbm.get_articles_byDays(cat, byDays=byDays)  # Use user-specified quantity
        if articles:
            df = pd.DataFrame(articles, columns=articles[0].keys())
            df = format_timestamps(df)
            st.dataframe(df)
            st.success(f"Retrieved {len(articles)} articles")
        else:
            st.info("No articles found")

        
# --- query/delete a specific article --- from here
st.markdown(
    """
    ---
    """
    )
article_id = st.number_input(
    "Article ID:",
    min_value=1,  # Only allow positive integers
    step=1,       # Increment/decrement by 1
    format="%d",  # Display as integer
    help="Enter the article ID you want to retrieve (must be a positive integer)"
)
col3, col4 = st.columns(2)
btn3, btn4 = st.columns([5,5])

with btn3:
    if st.button("Query Article"):
        article = dbm.get_article_byId(article_id)
        if article:
            for i, (key, value) in enumerate(article.items()):
                # Convert timestamp to local time if needed
                if key in ['created_at', 'updated_at'] and value is not None:
                    value = pd.to_datetime(value, utc=True).tz_convert('America/Los_Angeles').strftime('%Y-%m-%d %H:%M:%S')
                # Alternate between columns for better space usage
                if i % 2 == 0:
                    col3.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    col4.write(f"**{key.replace('_', ' ').title()}:** {value}")
            st.success(f"Retrieved article with ID: {article_id}")
        else:
            st.info("No article found")
with btn4:
    if st.button("Delete Article"):
        article = dbm.get_article_byId(article_id)
        if article:
            dbm.delete_article(article_id)
            st.success(f"Deleted article with ID: {article_id}")
        else:
            st.info("No article found")

# --- drop table --- from here
st.markdown(
    """
    ---
    """
    )

tbl = st.selectbox("Table:", [dbm.article_tbl])
if st.button("Drop Table"):
    dbm.drop_table(tbl)
    st.success(f"Dropped table: {tbl}")