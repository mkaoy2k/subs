"""
API for access Deta DB package with Streamlit cache
"""
import os, re
import datetime
import streamlit as st  # pip install streamlit
from deta import Deta  # pip install deta
from dotenv import load_dotenv  # pip install python-dotenv
import glog as log  # pip install glog
import pandas as pd # pip install pandas

# This is how to create/connect a database
@st.cache_resource
def connect_db():
    # Load the environment variables from file
    load_dotenv(".env")
    key = os.getenv("DETA_KEY")
    name = os.getenv("DETA_NAME")

    # Initialize with a project key
    deta = Deta(key)
    db = deta.Base(name)
    return db

db = connect_db()

def validate_username(username, min):
    """
    Check if username is not shorter than 'min' characters
    in length and is legitimate uaername
    Return True if passed else False
    """
    if len(username) < min:
        return False
    pattern = "^[a-zA-Z0-9]*$"
    if re.match(pattern, username):
        return True
    return False

def validate_email(email):
    """
    Check if email is legitimate.
    Return True if passed else False.
    """
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$" 

    if re.match(pattern, email):
        return True
    return False

def insert_user(username, fullname, email, password, l10n):
    """
    Return the user on a successful user creation, 
    otherwise raises an error.
    """
    # validate username, must not be sjorter than 4
    if not validate_username(username, 4):
        raise(KeyError)

    # validate email
    if not validate_email(email):
           raise(NameError)
    
    date_joined = str(datetime.datetime.now())

    return db.put({'key': username, 
                "fullname": fullname, 
                "email": email,                   
                'password': password, 
                'date_joined': date_joined,
                'l10n': l10n
                })

def fetch_users():
    """
    Fetch all users.
    Return a list of dictionaries, one dict per user
    """
    users = db.fetch()
    return users.items

# Clear all chches every 5 min = 300 seconds
@st.cache_data(ttl=300)
def get_usernames(base=None):
    """
    Fetch usernames
    Return List of user usernames
    """
    usernames = []
    for user in fetch_users():
        usernames.append(user['key'])
    return usernames

@st.cache_data(ttl=300)
def get_fullnames(base=None):
    """
    Fetch all user full names
    Return List of user emails:
    """
    fullnames = []
    for user in fetch_users():
        fullnames.append(user['fullname'])
    return fullnames

@st.cache_data(ttl=300)
def get_passwords(base=None):
    """
    Fetch all user emails
    Return List of user emails:
    """
    passwords = []
    for user in fetch_users():
        passwords.append(user['password'])
    return passwords

@st.cache_data(ttl=300)
def get_emails(base=None):
    """
    Fetch all user emails
    Return List of user emails:
    """
    emails = []
    for user in fetch_users():
        emails.append(user['email'])
    return emails

@st.cache_data(ttl=300)
def get_username(email, base=None):
    """
    Return username given by email
    """
    for user in fetch_users():
        if user['email'] == email:
            return user['key']
    return None
    
@st.cache_data(ttl=300)
def get_user(username, base=None):
    """
    Fetch an user, given by 'username' 
    and return a dict obj.
    If not found, the function will return None
    """
    try:
        user = db.get(username)
        return user
    except Exception as err:
        return None


def update_user(username, updates):
    """
    If the item is updated, return None. 
    Otherwise, an exception is raised.
    """
    return db.update(updates, username)


def delete_user(username):
    """
    Always return None, even if the key does not exist.
    """
    return db.delete(username)

if __name__ == '__main__':
    try:
        db = connect_db()
                        
        users = fetch_users()
        df = pd.DataFrame.from_dict(users)
        st.write(df)
        
        email = "mkaoy2k@yahoo.com"
        username = get_username(email)
        st.write(f"{email} belongs to {username}")
                 
        user = get_user(users[0]['key'])
        st.write(user)
                    
        usernames = get_usernames()
        df = pd.DataFrame(usernames, columns=['Username'])
        st.write(df)

        emails = get_emails()
        df = pd.DataFrame(emails, columns=['Email'])
        st.write(df)

    except Exception as err:
        st.error(f"Caught '{err}'. class is {type(err)}")

