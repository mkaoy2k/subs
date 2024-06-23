"""
API for access sqlite3 DB package with Streamlit cache
"""
import os, re
import datetime
import streamlit as st  # pip install streamlit
from dotenv import load_dotenv  # pip install python-dotenv
import glog as log  # pip install glog
import sqlite3
import pandas as pd # pip install pandas

# module global variables
# Load the environment variables from file
load_dotenv(".env")
dbn = os.getenv("DB_NAME")
user_tbl = os.getenv("TBL_NAME")
g_logging = os.getenv("LOGGING")
log.setLevel(g_logging)    

user_tbl_fields = ['key', 
              'fullname', 
              'email', 
              'password', 
              'date_joined', 
              'l10n']

# connect to a database/table
def connect_db():
    try:
        conn = sqlite3.connect(dbn)
    except Exception as err:
        log.error(f"Caught '{err}'. class is {type(err)}")
        raise err

    # create a table via SQL
    cmd = f"CREATE TABLE IF NOT EXISTS {user_tbl}"
    args = """ (
            key text,  
            fullname text,  
            email text,                          
            password text,     
            date_joined text,  
            l10n text)
            """
    sql_stmt = f"{cmd} {args}"
    try:
        c = conn.cursor()        
        c.execute(sql_stmt) 
        log.debug(f"{sql_stmt}")
    except Exception as err:
        log.error(f"Caught '{err}'. class is {type(err)}")
        raise err
    return conn

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
    with connect_db() as conn:   
        date_joined = str(datetime.datetime.now())
        cmd = f"INSERT INTO {user_tbl} VALUES"
        args = ''.join([
                    '("',username, 
                    '","', fullname,
                    '","', email,
                    '","', password,
                    '","', date_joined,
                    '","', l10n,
                    '")'])
        sql_stmt = f"{cmd} {args}"
        try:
            c = conn.cursor()
            c.execute(sql_stmt)
            log.debug(f"{sql_stmt}")
        except Exception as err:
            log.error(f"Caught '{err}'. class is {type(err)}")
            raise err
    return

# reload users from database every one hour = 3600 seconds
def fetch_users():
    """
    Fetch all users
    Return a list of dictionaries, one dict per user
    """

    # Get a new copy from Database
    with connect_db() as conn:
        # fetch all users in a list of user-dict-obj
        cmd = f"SELECT * FROM {user_tbl}"
        try:
            c = conn.cursor()
            c.execute(cmd)
            log.debug(f"{cmd}")

            # return list of tuples
            l_tup = c.fetchall()
            users = []
            for t in l_tup:
                l_val = list(t)
                d = dict(zip(user_tbl_fields, l_val))
                users.append(d)      
            return users
        except Exception as err:
            log.error(f"Caught '{err}'. class is {type(err)}")

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
    with connect_db() as conn:
        cmd = f"SELECT * FROM {user_tbl}"
        args = f"WHERE key='{username}'"
        sql_stmt = f"{cmd} {args}"
        try:
            c = conn.cursor()
            c.execute(f"{sql_stmt}")
            log.debug(f"{sql_stmt}")
            l_val = c.fetchone() # return None if no record
            if l_val:
                # get_user(username, return the user as a dict obj
                d = dict(zip(user_tbl_fields, l_val))
                return d
            else:
                return None
        except Exception as err:
            log.error(f"Caught '{err}'. class is {type(err)}")
            return None

def update_user(username, updates):
    """
    If the item is updated, return None. 
    Otherwise, an exception is raised.
    """

    if updates:
        with connect_db()as conn:
            cmd = f"UPDATE {user_tbl}" 
            args = "SET "
            for k, v in updates.items():
                if k == 'fullname':
                    args += f"fullname='{v}',"
                    continue
                if k == 'email':
                    args += f"email='{v}',"
                    continue
                if k == 'password':
                    args += f"password='{v}',"
                    continue
                if k == 'date_joined':
                    args += f"date_joined='{v}',"
                    continue
                if k == 'l10n':
                    args += f"l10n='{v}',"
                    continue
            args = args.strip(',')
            where = f"WHERE key='{username}'"
            sql_stmt = f"{cmd} {args} {where}"
            try:
                c = conn.cursor()
                c.execute(f"{sql_stmt}")
                log.debug(f"{sql_stmt}")
            except Exception as err:
                log.error(f"Caught '{err}'. class is {type(err)}")
                raise err
    else:
        return # do nothing

def delete_user(username):
    """
    Always return None, even if the key does not exist.
    """
    with connect_db() as conn:
        cmd = f"DELETE FROM {user_tbl}" 
        where = f"WHERE key='{username}'"
        sql_stmt = f"{cmd} {where}"
        try:
            c = conn.cursor()
            c.execute(f"{sql_stmt}")
            log.debug(f"{sql_stmt}")
        except Exception as err:
            log.error(f"Caught '{err}'. class is {type(err)}")

if __name__ == '__main__':
    try:                        
        users = fetch_users()
        df = pd.DataFrame.from_dict(users)
        st.write(df)
        
        email = "mkaoy2k@gmail.com"
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
