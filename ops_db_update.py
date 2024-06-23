import os, time
from dotenv import load_dotenv  # pip install python-dotenv
import streamlit as st
import streamlit_authenticator as stauth
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

def validate_pw(password1, password2):
    if len(password1) >= 6:
        if password1 == password2:
            # valid password
            return True
        else:
            st.warning("Passwords don't match.")
    else:
        st.warning("Password too short, min=6") 
    return False    

st.title("Update User Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    ---
    """
    )
g_dirtyUser = os.getenv("DIRTY_USER") 
log.debug(f"DIRTY_USER={g_dirtyUser}")   
username = st.text_input(':blue[Emter Username:]', 
            placeholder="Query an user record first, then click 'Update' or 'Delete'")
user = dbm.get_user(username, base=g_dirtyUser)
if user is not None:
    email = st.text_input(':blue[Email]', 
        user['email'],
        max_chars=50,
        help="Enter new email to update")

    password1 = st.text_input(':blue[Password]', 
            placeholder='Enter Your Password', type='password')
    password2 = st.text_input(':blue[Confirm Password]', 
            placeholder='Confirm Your Password', type='password')
    fullname = st.text_input(':blue[Full Name]', 
        user['fullname'],
        max_chars=50,
        help="Enter new fullname to update")
    lang_opt = ["繁中","US"]
    idx = lang_opt.index(user['l10n'])
    l10n = st.selectbox(f':blue[L10N]', 
            options=lang_opt, 
            index=idx,
            help="Select Your Language")
else:
    st.info(f"Username='{username}' Not Found. Please enter an username.")

btn1, btn2, btn3, btn4 = st.columns([2, 3, 3, 2])

with btn1:
    if st.button("Users"):
        users = dbm.get_usernames(base=g_dirtyUser)
        # keys as columns
        df = pd.DataFrame.from_dict(users, orient='columns')
        st.write(df)    

with btn2:
    if st.button("Passwords"):
        users = dbm.get_passwords(base=g_dirtyUser)
        # keys as columns
        df = pd.DataFrame.from_dict(users, orient='columns')
        st.write(df)    

with btn3:  
    if st.button("Update"):
        with st.spinner():
            upd = {}
            if email != user['email']:
                if not dbm.validate_email(email):
                    raise(NameError)
                upd['email'] = email
            if fullname != user['fullname']:
                upd['fullname'] = fullname
            if l10n != user['l10n']:
                upd['l10n'] = l10n
            if password1 or password2:
                if validate_pw(password1, password2):
                    hashed_password = stauth.Hasher([password2]).generate()
                    upd['password'] = hashed_password[0]
            if upd:
                st.write(upd)
                try:
                    dbm.update_user(username, upd)
                    st.success(f"Username='{username}' updated.")
                except Exception as err:
                    st.warning(f"Caught '{err}'. class is {type(err)}")
                    st.info(f"Username='{username}' failed to update.")
                    
with btn4:    
    if st.button("Delete"):     
        try:
            dbm.delete_user(username)
            st.success(f"Username='{username}' deleted.")
        except Exception as err:
            st.warning(f"Caught '{err}'. class is {type(err)}")
            st.info(f"Username='{username}' failed to delete.")

# force cache to create a new one every loop
os.environ['DIRTY_USER'] = str(time.time())

