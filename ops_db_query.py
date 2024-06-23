import os, time
from dotenv import load_dotenv  # pip install python-dotenv
import streamlit as st
import pandas as pd # pip install pandas
import glog as log  # pip install glog

# --- Initialize system environment --- from here
load_dotenv(".env")

# --- Set Server logging levels ---
g_logging = os.getenv("LOGGING")
log.setLevel(g_logging)    

# Import User database interface 
backend =  os.getenv("DB_SVR")
if backend == "deta":
    import sdb_deta as dbm    # using DeTa provider
elif backend == "sqlite3":
    import sdb_sqlite as dbm    # using sqlite3 module
else:
    raise(FileNotFoundError)
log.debug(f"DB_SVR import: {backend}")

st.title("Query User Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    ---
    """
    )
# Load the environment variables from '.env' file
load_dotenv(".env")
g_dirtyUser = os.getenv("DIRTY_USER")    

df = pd.DataFrame()
btn1, btn2, btn3 = st.columns([5,3,2])

try:
    with btn1:
        if st.button("All Users"):
            users = dbm.fetch_users()
            # keys as columns
            df = pd.DataFrame.from_dict(users, orient='columns')
            st.write(df)    
    with btn3:
        if st.button("Usernames"):
            usernames = dbm.get_usernames(base=g_dirtyUser)
            df = pd.DataFrame(usernames, columns=['Username'])
            st.write(df)    
    with btn2:
        if st.button("Emails"):
            emails = dbm.get_emails(base=g_dirtyUser)
            df = pd.DataFrame(emails, columns=['Email'])
            st.write(df)
                
    # --- query a specific user --- from here
    username = st.text_input(':blue[Username:]', 
                    placeholder='Enter Username to Query')
    if st.button("User Query"):
        user = dbm.get_user(username, base=g_dirtyUser)
        if user is not None:
            st.write(user)
            # keys as indeces
            df = pd.DataFrame.from_dict(user, orient='index')  
            st.write(df)          
        else:            
            st.info(f"Username='{username}' not found")
    # force cache to create a new one
    os.environ['DIRTY_USER'] = str(time.time())

except Exception as err:
    st.info(f"Caught '{err}'. class is {type(err)}")
