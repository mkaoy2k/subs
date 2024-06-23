import sys, os
from dotenv import load_dotenv  # pip install python-dotenv
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

n = len(sys.argv)

# check to expect 3 arguments as follows:
# username, email, and msg accordingly
if n != 4:
    print(f"Invalid Arguments {n}")
else:
    username = sys.argv[1]
    email = sys.argv[2]
    msg = sys.argv[3]

    user = dbm.get_user(username)
    if user is not None:
        # verify username is valid
        if username == user['key']:
            # verify email is correct
            if email != user['email']:
                print(f"Invalid Email {email}")
            else:
                upd = {}
                upd['password'] = msg
                try:
                    dbm.update_user(username, upd)
                    print("Done")
                except Exception as err:
                    print(f"Caught '{err}'. class is {type(err)}")
        else:
            print(f"Username: {username} vs key: {user['key']}")
    else:
        print(f"Username: {username} not found")
