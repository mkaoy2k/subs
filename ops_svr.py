"""
FamilyTree 網站操作伺服器

此模組提供 FamilyTree 網站的後端服務，包括用戶激活、常見問題和關於頁面的多語言支援。

主要功能：
- 用戶帳號激活
- 多語言支援 (L10N)
- 常見問題 (FAQ) 頁面
- 關於頁面

方法 1: 直接運行
python ops_svr.py

方法 2: 使用 Flask 命令
flask --app ops_svr run -p 8501
"""

from flask import Flask, request, redirect, render_template, flash, url_for, session
from flask_mail import Mail
import secrets
import os
from dotenv import load_dotenv
from db_utils import add_subscriber, remove_subscriber, verify_token as db_verify_token
from email_utils import validate_email, generate_verification_token, send_verification_email, Config
from funcUtils import *
import subprocess
from dotenv import load_dotenv  # pip install python-dotenv
import logging

# 載入環境變數
load_dotenv(".env")

# Configure logging
log = logging.getLogger(__name__)
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

# Remove any existing handlers to avoid duplicates
log.handlers = []

# Configure console handler with the desired format
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to our logger
log.addHandler(console_handler)

# Prevent propagation to root logger
log.propagate = False

# Configure Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # Required for session management

# Configure Flask-Mail with SSL on port 465
app.config.update(
    # Basic settings
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@familytree.com'),
    # Additional settings for better reliability
    MAIL_DEBUG=0,  # Set to 1 for SMTP debug output
    MAIL_SUPPRESS_SEND=False
)

# Initialize Flask-Mail
mail = Mail(app)

# Test email configuration
log.info(f"Email server configured: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
log.info(f"Using TLS: {app.config['MAIL_USE_TLS']}, Using SSL: {app.config['MAIL_USE_SSL']}")

def init_globals():
    """
    初始化全局變數
    
    包含：
    - 載入環境變數
    - 設定日誌級別
    - 初始化多語言支援 (L10N)
    - 載入選單和頁面內容
    
    Returns:
        tuple: 包含所有全局變數的元組
    """
    # 載入資料庫後端設定
    backend = os.getenv("DB_SVR")
    log.debug(f"DB_SVR import: {backend}")
    
    # 設定 FamilyTrees 伺服器端點
    ft_svr = os.getenv("FT_SVR")
    log.debug(f"FamilyTrees Server: {ft_svr}")    
    
    # 載入多語言支援
    l10n_file = os.getenv("L10N_FILE")    
    g_L10N = load_L10N(l10n_file)
    g_L10N_options = list(g_L10N.keys())
    
    # 初始化系統語言設定
    g_loc_key = os.getenv("L10N")
    g_loc = g_L10N[g_loc_key]
    log.debug(f"L10N='{g_loc_key}'...")
    
    # 載入選單
    f_menu = os.getenv("OPS_MENU_FILE")
    g_MENU = load_menu(f_menu)
    g_menu = g_MENU[f"{g_loc_key}"]
    
    # 初始化所有語言的頁面內容
    g_PAGE = {}
    for loc in g_L10N_options:
        key = g_L10N_options.index(loc)
        l_page = {}
        l_loc = g_L10N[loc]
        
        # 初始化 home page
        l_home = {
            't1_joke': "".join(l_loc['HOME_HTML_T1_JOKES']),
            't2_motto': "".join(l_loc['HOME_HTML_T2_MOTTO']),
        }
        l_page['home'] = l_home
        
        # 初始化常見問題頁面
        l_faq = {
            'download': "".join(l_loc['FAQ_DOWNLOAD']),
            'charge': "".join(l_loc['FAQ_CHARGE']),
            'donate': "".join(l_loc['FAQ_DONATE']),
            'creator': "".join(l_loc['FAQ_CREATOR'])
        }
        l_page['faq'] = l_faq
        
        # 初始化關於頁面
        l_about = {
            'abs': "".join(l_loc['ABOUT_HTML_ABS']),
            'use': "".join(l_loc['ABOUT_USAGE']),
            'signup': "".join(l_loc['ABOUT_SIGNUP']),
            'login': "".join(l_loc['ABOUT_LOGIN']),
            'resetpw': "".join(l_loc['ABOUT_RESETPW']),
            'settings': "".join(l_loc['ABOUT_SETTINGS']),
            'fb': "".join(l_loc['ABOUT_FB']),
            'safety': "".join(l_loc['ABOUT_SAFETY']),
            'backup': "".join(l_loc['ABOUT_BACKUP']),
            'sharing': "".join(l_loc['ABOUT_SHARING']),
            'mls': "".join(l_loc['ABOUT_MLS'])
        }
        l_page['about'] = l_about
        g_PAGE[key] = l_page
    
    # 設定當前語言的頁面內容
    key = g_L10N_options.index(g_loc_key)
    g_home = g_PAGE[key]['home']
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    
    return (backend, ft_svr, g_L10N, g_L10N_options,
            g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about)

# 初始化全局變數
(backend, ft_svr, g_L10N, g_L10N_options,
 g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, 
 g_home, g_faq, g_about) = init_globals()

@app.route("/")
def home():
    """
    首頁路由
    
    Returns:
        str: 渲染後的首頁 HTML
    """
    global g_loc, g_L10N_options, g_menu

    return render_template('home.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['HOME_HTML_H1'],
        t1=g_loc['HOME_HTML_T1'],
        t1_joke=g_home['t1_joke'],
        t2=g_loc['HOME_HTML_T2'],
        t2_motto=g_home['t2_motto'],
        t3=g_loc['HOME_HTML_T3'],
        t3_user=g_loc['HOME_HTML_T3_USER'],
        t3_download=g_loc['HOME_HTML_T3_DOWNLOAD'],
        title='home')

@app.route("/faq")
def faq():
    """
    常見問題 (FAQ) 頁面路由
    
    此路由負責渲染並返回常見問題頁面，顯示系統的使用說明和常見問題解答。
    頁面內容支援多語言，根據用戶的語言設定自動切換。
    
    Returns:
        str: 渲染後的 FAQ 頁面 HTML 內容
        
    全局變數:
        g_loc (dict): 當前語系的本地化字串
        g_L10N_options (list): 可用的語言選項
        g_menu (dict): 導航菜單項目
        g_faq (dict): 常見問題內容
        
    模板文件:
        faq.html: 用於渲染 FAQ 頁面的模板
    """
    global g_loc, g_L10N_options, g_menu, g_faq
    
    return render_template('faq.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['FAQ_HTML_H1'],
        faq_download_q=g_loc['FAQ_DOWNLOAD_Q'],
        faq_download=g_faq['download'],
        faq_charge_q=g_loc['FAQ_CHARGE_Q'],
        faq_charge=g_faq['charge'],
        faq_donate_q=g_loc['FAQ_DONATE_Q'],
        faq_donate=g_faq['donate'],
        faq_creator_q=g_loc['FAQ_CREATOR_Q'],
        faq_creator=g_faq['creator'],
        title='faq')

@app.route("/about")
def about():
    """
    
    Returns:
        Response: About FamilyTree 主網站
    """
    global g_loc, g_L10N_options, g_menu, g_about
    
    return render_template('About.html',
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
    """
    設置語言本地化 (L10N) 路由
    
    根據 URL 參數切換網站顯示語言
    
    Query Parameters:
        lang (str): 語言代碼
        page (str): 當前頁面 ('faq' 或 'about')
        
    Returns:
        Response: 重新導向到當前頁面的新語言版本
    """
    global g_loc_key, g_loc, g_L10N_options
    global g_MENU, g_menu, g_PAGE, g_faq, g_about, g_home
    
    # 從 URL 參數獲取語言和頁面
    g_loc_key = request.args.get('lang')
    page = request.args.get('page', 'home')  # 預設為 home 頁面
    
    try:
        # 更新選單語言
        g_menu = g_MENU[g_loc_key]
        log.debug(f"Menu={g_menu}...")
        
        # 更新本地化設定
        g_loc = g_L10N[g_loc_key]
        log.debug(f"L10N='{g_loc_key}'...")
        
        # 更新頁面內容
        key = g_L10N_options.index(g_loc_key)
        g_faq = g_PAGE[key]['faq']
        g_about = g_PAGE[key]['about']
        g_home = g_PAGE[key]['home']
        
        # 返回相應頁面
        if page == "about":
            return about()
        elif page == "faq":
            return faq()
        else:
            return home()
        
    except (KeyError, ValueError) as e:
        log.error(f"語言切換錯誤: {str(e)}")
        # 如果出現錯誤，重定向到首頁
        return redirect(f"{ft_svr}")


def main():
    """
    主函數
    
    啟動 Flask 開發伺服器
    """
    log.info("啟動 FamilyTree 操作伺服器...")
    app.run(debug=True, port=8501)


@app.route('/subscribe', methods=['POST'])
def subscribe():
    """
    處理郵件訂閱/退訂請求
    
    Returns:
        Response: 重定向回上一頁並顯示操作結果
    """
    email = request.form.get('email')
    action = request.form.get('action')
    
    if not validate_email(email):
        flash('Please enter a valid email address', 'danger')
        return redirect(request.referrer or url_for('home'))
    
    try:
        if action == 'subscribe':
            # Generate verification token
            token = generate_verification_token()
            # Send verification email
            if send_verification_email(mail, email, token, is_subscribe=True, max_retries=3):
                flash('Please check your email to confirm your subscription.', 'info')
                add_subscriber(email, token)
            else:
                flash('Failed to send verification email. Please try again later.', 'danger')
        else:
            # For unsubscribe, we can either send a verification email or directly unsubscribe
            # Here we'll send a verification email for security
            token = generate_verification_token()
            if send_verification_email(mail, email, token, is_subscribe=False, max_retries=3):
                flash('Please check your email to confirm unsubscription.', 'info')
            else:
                flash('Failed to send verification email. Please try again later.', 'danger')
                
    except Exception as e:
        log.error(f"Error processing subscription: {str(e)}")
        flash('An error occurred. Please try again later.', 'danger')
    
    return redirect(request.referrer or url_for('home'))


@app.route('/verify-email')
def verify_email():
    """
    Verify email subscription/unsubscription
    """
    email = request.args.get('email')
    token = request.args.get('token')
    action = request.args.get('action')
    
    if not all([email, token, action]):
        flash('Invalid verification link', 'danger')
        return redirect(url_for('home'))
    
    # Verify the token
    if not db_verify_token(email, token):
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('home'))
    
    # Process subscription/unsubscription
    if action == 'subscribe':
        add_subscriber(email, token)
        flash('You have been successfully subscribed to our newsletter!', 'success')
    else:
        remove_subscriber(email)
        flash('You have been unsubscribed from our newsletter.', 'info')
    
    return redirect(url_for('home'))


if __name__ == "__main__":
    main()
