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

st.title("Purge Article Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    """
    )
cats = dbm.get_article_categories()
cat = st.selectbox("Category:", cats)

col1, col2 = st.columns(2)
with col1:
    # 添加數字輸入框，預設值為10，最小值為1，最大值為100
    limit = st.number_input(
        "Number of articles to fetch:",
        min_value=1,
        step=1,
        format="%d",
        help="Enter the number of articles you want to retrieve (1-100)"
    )
with col2:
    # query articles by last numberr of days
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
        articles = dbm.get_articles(cat, limit=limit)  # 使用使用者輸入的數量
        if articles:
            df = pd.DataFrame(articles, columns=articles[0].keys())
            df = format_timestamps(df)
            st.dataframe(df)
            st.success(f"Retrieved {len(articles)} articles")
        else:
            st.info("No articles found")    

with btn2:
    if st.button("Query by days"):
        articles = dbm.get_articles_byDays(cat, byDays=byDays)  # 使用使用者輸入的數量
        if articles:
            df = pd.DataFrame(articles, columns=articles[0].keys())
            df = format_timestamps(df)
            st.dataframe(df)
            st.success(f"Retrieved {len(articles)} articles")
        else:
            st.info("No articles found")

        
# --- query a specific article --- from here
st.markdown(
    """
    ---
    """
    )
article_id = st.number_input(
    "Article ID:",
    min_value=1,  # 只允許正整數
    step=1,       # 每次增減1
    format="%d",  # 顯示為整數
    help="Enter the article ID you want to retrieve (must be a positive integer)"
)
col3, col4 = st.columns(2)
btn3, btn4 = st.columns([5,5])

with btn3:
    if st.button("Article Query"):
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
    if st.button("Article Delete"):
        article = dbm.get_article_byId(article_id)
        if article:
            dbm.delete_article(article_id)
            st.success(f"Deleted article with ID: {article_id}")
        else:
            st.info("No article found")
