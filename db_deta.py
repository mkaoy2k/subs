"""
API for access Deta DB package
"""
import os, re
import datetime
from deta import Deta  # pip install deta
from dotenv import load_dotenv  # pip install python-dotenv
import glog as log  # pip install glog

# This is how to create/connect a database
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

# reload users from database every one hour = 3600 seconds
def fetch_users():
    """
    Fetch all users
    Return a dict of all users
    """
    users = db.fetch()
    return users.items

def get_usernames():
    """
    Fetch usernames
    Return List of user usernames
    """
    usernames = []
    for user in fetch_users():
        usernames.append(user['key'])
    return usernames

def get_fullnames():
    """
    Fetch all user full names
    Return List of user emails:
    """
    fullnames = []
    for user in fetch_users():
        fullnames.append(user['fullname'])
    return fullnames

def get_passwords():
    """
    Fetch all user emails
    Return List of user emails:
    """
    passwords = []
    for user in fetch_users():
        passwords.append(user['password'])
    return passwords

def get_emails():
    """
    Fetch all user emails
    Return List of user emails:
    """
    emails = []
    for user in fetch_users():
        emails.append(user['email'])
    return emails

def get_user(username):
    """
    Fetch an user, given by 'username' 
    and return a dict obj.
    If not found, the function will return None
    """
    return db.get(username)

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

