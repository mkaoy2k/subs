from flask import Flask, request, redirect, render_template
import os, subprocess
from dotenv import load_dotenv  # pip install python-dotenv
import glog as log  # pip install glog
from funcUtils import *

# --- Initialize system environment --- from here
load_dotenv(".env")

# --- Set Server logging levels ---
g_logging = os.getenv("LOGGING")
log.setLevel(g_logging)   

# Import User database interface 
backend =  os.getenv("DB_SVR")
log.debug(f"DB_SVR import: {backend}")

# --- Set endpoint for FamilyTrees Server ---
ft_svr = os.getenv("FT_SVR")
log.debug(f"FamilyTrees Server: {ft_svr}")    

# --- global L10N dictionary --- from here
# Load 'g_L10N', for all languages
# Load global list, 'g_L10N_options', for all languages
g_dirtyUser = os.getenv("DIRTY_USER")    

g_L10N = load_L10N(base=g_dirtyUser)
g_L10N_options = list(g_L10N.keys())

# --- Initialize System L10N Settings ---- from here
# set system L10N setting as default locator key , 'g_loc_key'
# and associated language dictionary, 'g_loc'
g_loc_key = os.getenv("L10N")    
g_loc = g_L10N[g_loc_key]
log.debug(f"L10N='{g_loc_key}'...")    

# initialize the main menu
f_menu = os.getenv("OPS_MENU_FILE")
g_MENU = load_menu(f_menu)
g_menu = g_MENU[f"{g_loc_key}"]
# log.debug(f"Menu={g_menu}...")

g_PAGE = {}
# for each language, initialize 'faq' and 'about' pages    
for loc in g_L10N_options:
    key = g_L10N_options.index(loc)
    l_page = {}
    l_loc =g_L10N[loc]
    # initialize 'faq' page
    l_faq = {}
    l_faq['charge'] = "".join(l_loc['FAQ_CHARGE'])
    l_faq['donate'] = "".join(l_loc['FAQ_DONATE'])
    l_faq['creator'] = "".join(l_loc['FAQ_CREATOR'])
    l_page['faq'] = l_faq 
    
    # initialize 'about' page
    l_about = {}
    l_about['abs'] = "".join(l_loc['ABOUT_HTML_ABS'])
    l_about['use'] = "".join(l_loc['ABOUT_USAGE'])
    l_about['signup'] = "".join(l_loc['ABOUT_SIGNUP'])
    l_about['login'] = "".join(l_loc['ABOUT_LOGIN'])
    l_about['resetpw'] = "".join(l_loc['ABOUT_RESETPW'])
    l_about['settings'] = "".join(l_loc['ABOUT_SETTINGS'])
    l_about['fb'] = "".join(l_loc['ABOUT_FB'])
    l_about['safety'] = "".join(l_loc['ABOUT_SAFETY'])
    l_about['backup'] = "".join(l_loc['ABOUT_BACKUP'])
    l_about['sharing'] = "".join(l_loc['ABOUT_SHARING'])
    l_about['mls'] = "".join(l_loc['ABOUT_MLS'])
    l_page['about'] = l_about 
    
    # store in g_PAGE
    g_PAGE[key] = l_page

# initialize faq page
key = g_L10N_options.index(g_loc_key)
g_faq = g_PAGE[key]['faq']
# log.debug(f"FAQ={g_faq}")

# initialize about page
g_about = g_PAGE[key]['about']
# log.debug(f"About={g_about}")

# --- Flask Web Server --- from here
app = Flask(__name__)

@app.route("/")
def home():
    return redirect(f"{ft_svr}")
 
@app.route("/activate")
def activate():
    username = request.args.get('username')
    email = request.args.get('email')
    msg = request.args.get('msg')
    # launch a sub-process, executing a Python script
    # and return result in a byte string
    s1 = subprocess.check_output(['python', 
                                  'ops_activate.py', 
                                  username, email, msg])
    if s1 == b'Done\n':
        return redirect(f"{ft_svr}")
    else:
        # map to normal string
        rtn = s1.decode('ASCII')
        resp = f"<h1>{username}:</h1>\n<h2>{rtn}</h2>"
        return resp

@app.route("/faq")
def faq():
    global g_loc, g_L10N_options
    global g_menu, g_faq

    return render_template('faq.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['FAQ_HTML_H1'],
        faq_charge_q=g_loc['FAQ_CHARGE_Q'],
        faq_charge=g_faq['charge'],
        faq_donate_q=g_loc['FAQ_DONATE_Q'],
        faq_donate=g_faq['donate'],
        faq_creator_q=g_loc['FAQ_CREATOR_Q'],
        faq_creator=g_faq['creator'],
        title='faq')

@app.route("/about")
def about():
    global g_loc, g_L10N_options
    global g_menu, g_about
    
    return render_template('about.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['ABOUT_HTML_H1'],
        abs_header=g_loc['ABOUT_ABS_H2'],
        abs=g_about['abs'],
        usage_header=g_loc['ABOUT_USAGE_H2'],
        usage=g_about['use'],
        signup_q=g_loc['ABOUT_SIGNUP_Q'],
        signup=g_about['signup'],
        login_q=g_loc['ABOUT_LOGIN_Q'],
        login=g_about['login'],
        resetpw_q=g_loc['ABOUT_RESETPW_Q'],
        resetpw=g_about['resetpw'],
        settings_q=g_loc['ABOUT_SETTINGS_Q'],
        settings=g_about['settings'],
        fb_header=g_loc['ABOUT_FB_H2'],
        fb=g_about['fb'],
        fb_safety=g_loc['ABOUT_FB_SAFETY'],
        safety=g_about['safety'],
        fb_backup=g_loc['ABOUT_FB_BACKUP'],
        backup=g_about['backup'],
        fb_sharing=g_loc['ABOUT_FB_SHARING'],
        sharing=g_about['sharing'],
        fb_mls=g_loc['ABOUT_FB_MLS'],
        mls=g_about['mls'],
        title='about')
    
@app.route("/setL10N")
def set_l10n():
    global g_loc_key, g_loc, g_L10N_options
    global g_MENU, g_menu
    global g_PAGE, g_faq, g_about
    
    # expect two parms
    g_loc_key = request.args.get('lang')
    page = request.args.get('page')

    # reset main menu accordingly
    g_menu = g_MENU[f"{g_loc_key}"]
    log.debug(f"Menu={g_menu}...")
    
    # set L10N
    g_loc = g_L10N[g_loc_key]
    log.debug(f"L10N='{g_loc_key}'...")    
    
    # set pages according to lang
    key = g_L10N_options.index(g_loc_key)
    
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    if page == "faq":
        # return 'faq' page
        return faq()
    else:
        # default page == "about":
        return about()

            
if __name__ == "__main__":
    # Run cmd:
    # flask --app ops_svr run -p 5555
    app.run(debug=True)
