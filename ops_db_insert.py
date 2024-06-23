import os, time
from dotenv import load_dotenv  # pip install python-dotenv
import streamlit as st
import streamlit_authenticator as stauth
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

# Define User class
class User:
    """ User class """

    def __init__(self, 
            username,      # uaername
            fullname,      # fullname
            email,         # email                  
            password,      # password
            l10n           # l10n
            ):
        self.key = username
        self.fullname = fullname
        self.email = email
        self.password = password
        self.l10n = l10n

    def to_dict(self):
        d = {}
        d['key'] = self.key
        d['fullname'] = self.fullname
        d['email'] = self.email
        d['password'] = self.password
        d['l10n'] = self.l10n
        return d
    
    def __repr__(self):
        return "User('{}', '{}', '{}')".format(self.key, 
                                               self.fullname, 
                                               self.email, 
                                               self.password, 
                                               self.l10n)
        
st.title("Insert into User Database")
st.markdown(
    """
    ##### *Created with ❤️ by* [Michael Kao](https://github.com/mkaoy2k):sunglasses:
    ---
    """
    )
# Load the environment variables from '.env' file
load_dotenv(".env")
g_dirtyUser = os.getenv("DIRTY_USER")    

user1 = User("mkao",
             "Michael Kao",
             "mkaoy2k@me.com",
             "abc1342",
             "繁中"
             )
user2 = User("jkao",
             "Joy Kao",
             "mkaoy2k@gmail.com",
             "abc1342",
             "US"             
            )
users = [user1, user2]

usernames = []
fullnames = []
emails = []
passwords = []
l10ns = []
for user in users:
    usernames.append(user.key)
    fullnames.append(user.fullname)
    emails.append(user.email)
    passwords.append(user.password)
    l10ns.append(user.l10n)

st.write(usernames)
st.write(fullnames)
st.write(emails)
st.write(passwords)
st.write(l10ns)

if st.button("Insert"):
    hashed_passwords = stauth.Hasher(passwords).generate()

    for username in usernames:
        try:
            dbm.delete_user(username)
            st.success(f'{username} deleted.')
        except Exception as err:
            st.warning(f"Caught '{err}'. class is {type(err)}")
            st.warning(f'{username} failed to delete.')
            continue

    for (username, fullname, email, hashed_password, l10n) in zip(
        usernames, fullnames, emails, hashed_passwords, l10ns):
        try:
            dbm.insert_user(username, fullname, email, 
                            hashed_password, l10n)
            user = dbm.get_user(username)
            st.write(user)
            st.success(f'{username} inserted.')
        except Exception as err:
            st.warning(f"Caught '{err}'. class is {type(err)}")
            st.warning(f'{username} failed to insert.')
            continue
    # force to create a new UserDB cache upon return
    os.environ['DIRTY_USER'] = str(time.time())

