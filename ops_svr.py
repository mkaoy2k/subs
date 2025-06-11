"""
FamilyTrees 營運伺服器

此模組提供 FamilyTrees 網站的後端服務，包括用戶激活、常見問題和關於頁面的多語言支援。

主要功能：
- 用戶帳號激活
- 多語言支援 (L10N)
- 常見問題 (FAQ) 頁面
- 關於頁面

方法 1: 直接運行
python ops_svr.py

方法 2: 使用 Flask 命令
flask --app ops_svr run -p 5555
"""

from flask import Flask, request, redirect, render_template, flash, url_for, session, jsonify
from flask_mail import Mail
import secrets
import os
from dotenv import load_dotenv
from db_utils import add_subscriber, remove_subscriber, verify_token, get_subscribers, get_article
from email_utils import validate_email, generate_verification_token, send_verification_email, send_newsletter
from funcUtils import load_menu, load_L10N
import subprocess
from dotenv import load_dotenv  # 安裝: pip install python-dotenv
import logging

# 載入環境變數
load_dotenv(".env")

# 配置日誌記錄
log = logging.getLogger(__name__)
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

# 移除現有的處理程序以避免重複
log.handlers = []

# 配置控制台處理程序的格式
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 將處理程序添加到日誌記錄器
log.addHandler(console_handler)

# 防止傳播到根日誌記錄器
log.propagate = False

# 配置 Flask 應用程序
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # 會話管理所需

# 在 465 端口上配置帶有 SSL 的 Flask-Mail
app.config.update(
    # 基本設置
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@familytree.com'),
    # 提高可靠性的其他設置
    MAIL_DEBUG=0,  # 設置為 1 可獲取 SMTP 調試輸出
    MAIL_SUPPRESS_SEND=False
)

# 初始化 Flask-Mail
mail = Mail(app)

# 測試電子郵件配置
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
    backend = os.getenv("DB_SVR", "sqlite3")
    log.debug(f"DB_SVR import: {backend}")
    
    # 設定 FamilyTrees 伺服器端點
    ft_svr = os.getenv("FT_SVR", "https://crappie-on-kingfish.ngrok-free.app")
    log.debug(f"FamilyTrees Server: {ft_svr}")    
    git_ftpe = os.getenv("GIT_FTPE", "https://github.com/mkaoy2k/ftpe.git")
    log.debug(f"ftpe GitHub Server: {git_ftpe}")
    git_subs = os.getenv("GIT_SUBS", "https://github.com/mkaoy2k/subs.git")
    log.debug(f"subs GitHub Server: {git_subs}")
    
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
        cats = [l_loc['HOME_HTML_T1'], 
                l_loc['HOME_HTML_T2'],
                l_loc['HOME_HTML_T3']
                ]
        l_home = {}
        for idx, cat in enumerate(cats, 1):
            article = get_article(cat)
            if article:
                l_home[str(idx)] = {
                    "title": article.get('title', ''),
                    "content": article.get('content', ''),
                    "image": article.get('image_url', '')
                }
            else:
                l_home[str(idx)] = {
                    "title": "",
                    "content": "",
                    "image": ""
                }
                log.debug(f"No article found in category: {cat}")
        l_page['home'] = l_home
        
        # 初始化常見問題頁面
        l_faq = {
            'ops_down': "".join(l_loc['FAQ_OPS_DOWN']),
            'download': "".join(l_loc['FAQ_DOWNLOAD']),
            'charge': "".join(l_loc['FAQ_CHARGE']),
            'donate': "".join(l_loc['FAQ_DONATE']),
            'creator': "".join(l_loc['FAQ_CREATOR'])
        }
        l_page['faq'] = l_faq
        
        # 初始化關於頁面
        l_about = {
            'abs1': "".join(l_loc['ABOUT_HTML_ABS1']),
            'abs2': "".join(l_loc['ABOUT_HTML_ABS2']),
            'abs3': "".join(l_loc['ABOUT_HTML_ABS3']),
            'abs4': "".join(l_loc['ABOUT_HTML_ABS4'])
        }
        l_page['about'] = l_about
        g_PAGE[key] = l_page
    
    # 設定當前語言的頁面內容
    key = g_L10N_options.index(g_loc_key)
    g_home = g_PAGE[key]['home']
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    
    return (backend, ft_svr, git_ftpe, git_subs, g_L10N, g_L10N_options,
            g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about)

# 初始化全局變數
(backend, ft_svr, git_ftpe, git_subs, g_L10N, g_L10N_options,
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

    t1_image = g_home['1']['image']
    t1_image_alt = t1_image.split('/')[-1] if t1_image else ''
    t2_image = g_home['2']['image']
    t2_image_alt = t2_image.split('/')[-1] if t2_image else ''
    t3_image = g_home['3']['image']
    t3_image_alt = t3_image.split('/')[-1] if t3_image else ''
    
    return render_template('home.html',
        menu=g_menu,
        options=g_L10N_options,
        settings=g_loc['SETTINGS'],
        your_language=g_loc['YOUR_LANGUAGE'],
        subscribe=g_loc['SUBSCRIBE'],
        unsubscribe=g_loc['UNSUBSCRIBE'],
        email_subscription=g_loc['EMAIL_SUBSCRIPTION'],
        header=g_loc['HOME_HTML_H1'],
        h2=g_loc['HOME_HTML_H2'],
        motto=g_loc['HOME_HTML_MOTTO'],
        ft_url=ft_svr,
        t1=g_loc['HOME_HTML_T1'],
        t1_title=g_home['1']['title'],
        t1_content=g_home['1']['content'],
        t1_image=t1_image,
        t1_image_alt=t1_image_alt,
        t2=g_loc['HOME_HTML_T2'],
        t2_title=g_home['2']['title'],
        t2_content=g_home['2']['content'],
        t2_image=t2_image,
        t2_image_alt=t2_image_alt,
        t3=g_loc['HOME_HTML_T3'],
        t3_title=g_home['3']['title'],
        t3_content=g_home['3']['content'],
        t3_image=t3_image,
        t3_image_alt=t3_image_alt,
        t4_greeting=g_loc['HOME_HTML_T4_GREETING'],
        t4_team=g_loc['HOME_HTML_T4_TEAM'],
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
    global g_loc, g_L10N_options, g_menu, g_faq, ft_svr
    
    return render_template('faq.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['FAQ_HTML_H1'],
        faq_ops_down_q=g_loc['FAQ_OPS_DOWN_Q'],
        faq_ops_down=g_faq['ops_down'],
        faq_download_q=g_loc['FAQ_DOWNLOAD_Q'],
        faq_download=g_faq['download'],
        faq_try_demo=g_loc['FAQ_TRY_DEMO'],
        ft_url=ft_svr,
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
    global g_loc, g_L10N_options, g_menu, g_about, git_ftpe, git_subs
    
    return render_template('About.html',
        menu=g_menu,
        options=g_L10N_options,
        header=g_loc['ABOUT_HTML_H1'],
        abs_header=g_loc['ABOUT_ABS_H2'],
        abs1=g_about['abs1'],
        abs2=g_about['abs2'],
        abs3=g_about['abs3'],
        abs4=g_about['abs4'],
        git_repo=g_loc['ABOUT_USAGE_H2'],
        git_ftpe=git_ftpe,
        git_subs=git_subs,
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
            # 生成驗證令牌
            token = generate_verification_token()
            # 發送驗證郵件
            if send_verification_email(mail, email, token, is_subscribe=True):
                flash('Please check your email to confirm your subscription.', 'info')
                add_subscriber(email, token)
            else:
                flash('Failed to send verification email. Please try again later.', 'danger')
        else:
            # 對於退訂，我們可以發送驗證郵件或直接退訂
            # 為了安全起見，我們在這裡發送驗證郵件
            token = generate_verification_token()
            if send_verification_email(mail, email, token, is_subscribe=False):
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
    驗證電子郵件訂閱/退訂
    """
    email = request.args.get('email')
    token = request.args.get('token')
    action = request.args.get('action')
    
    if not all([email, token, action]):
        log.debug(f"Invalid verification link: {email}, {token}, {action}")
        flash('Invalid verification link', 'danger')
        return redirect(url_for('home'))
    
    # 驗證令牌
    if not verify_token(email, token):
        log.debug(f"Invalid or expired verification link: {email}, {token}, {action}")
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('home'))
    
    # 處理訂閱/退訂
    if action == 'subscribe':
        add_subscriber(email, token)
        flash('You have been successfully subscribed to our newsletter!', 'success')
    else:
        remove_subscriber(email)
        flash('You have been unsubscribed from our newsletter.', 'info')
    
    return redirect(url_for('home'))

# ---- Internal tools below ----
@app.route('/dbq')
def db_query():
    """通過運行 ops_db_query.py 作為子進程執行數據庫查詢。
    
    返回:
        Response: 包含查詢結果或錯誤訊息的 JSON 回應
    """
    import subprocess
    import json
    import os
    
    try:
        # 獲取當前腳本所在目錄
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'ops_db_query.py')
        
        # 運行腳本並不捕獲輸出
        subprocess.run(
            ['.venv/bin/streamlit', 'run', script_path],
            capture_output=False,
            text=True,
            check=True
        )
            
    except subprocess.CalledProcessError as e:
        flash(jsonify({
            'status': 'error',
            'message': 'Script execution failed',
            'error': str(e),
            'stdout': e.stdout,
            'stderr': e.stderr
        }), 'danger')
        
    except Exception as e:
        flash(jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'error': str(e)
        }), 'danger')
    return redirect(url_for('home'))

@app.route('/dbu')
def db_update():
    """通過運行 ops_db_update.py 作為子進程執行數據庫更新。
    
    返回:
        Response: 包含更新結果或錯誤訊息的 JSON 回應
    """
    import subprocess
    import json
    import os
    
    try:
        # 獲取當前腳本所在目錄
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'ops_db_update.py')
        
        # 運行腳本並不捕獲輸出
        subprocess.run(
            ['.venv/bin/streamlit', 'run', script_path],
            capture_output=False,
            text=True,
            check=True
        )
            
    except subprocess.CalledProcessError as e:
        flash(jsonify({
            'status': 'error',
            'message': 'Update script execution failed',
            'error': str(e),
            'stdout': e.stdout,
            'stderr': e.stderr
        }), 'danger')
        
    except Exception as e:
        flash(jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred during update',
            'error': str(e)
        }), 'danger')
    
    return redirect(url_for('home'))

@app.route('/pub')
def pub_newsletter():
    """
    retrieve active subscribers' emails from db and send newsletter
    """
    global g_loc, g_home, g_loc_key
    
    users = get_subscribers(state='active')
    if not users:  # Handles both None and empty list
        flash('No active subscribers found', 'warning')
        return redirect(url_for('home'))
        
    emails = [user['email'] for user in users if user and 'email' in user]
    if not emails:  # In case all users in the list are invalid or missing email
        flash('No valid email addresses found', 'warning')
        return redirect(url_for('home'))

    t1_image = g_home['1']['image']
    t1_image_alt = t1_image.split('/')[-1] if t1_image else ''
    t2_image = g_home['2']['image']
    t2_image_alt = t2_image.split('/')[-1] if t2_image else ''
    t3_image = g_home['3']['image']
    t3_image_alt = t3_image.split('/')[-1] if t3_image else ''
        
    # create blob dictionary
    blob = {
        'header': g_loc['HOME_HTML_H1'],
        'h2': g_loc['HOME_HTML_H2'],
        'motto': g_loc['HOME_HTML_MOTTO'],
        'ft_url': ft_svr,
        't1': g_loc['HOME_HTML_T1'],
        't1_title': g_home['1']['title'],
        't1_content': g_home['1']['content'],
        't1_image': t1_image,
        't1_image_alt': t1_image_alt,
        't2': g_loc['HOME_HTML_T2'],
        't2_title': g_home['2']['title'],
        't2_content': g_home['2']['content'],
        't2_image': t2_image,
        't2_image_alt': t2_image_alt,
        't3': g_loc['HOME_HTML_T3'],
        't3_title': g_home['3']['title'],
        't3_content': g_home['3']['content'],
        't3_image': t3_image,
        't3_image_alt': t3_image_alt,
        't4_greeting': g_loc['HOME_HTML_T4_GREETING'],
        't4_team': g_loc['HOME_HTML_T4_TEAM'],
        'title': 'newsletter'
    }
    try:
        if send_newsletter(mail, emails, blob):
            flash('Newsletter sent successfully', 'success')
        else:
            flash('Newsletter sent failed', 'danger')
    except Exception as e:
        flash('Newsletter sent failed', 'danger')
    return redirect(url_for('home'))    

def main():
    """
    主函數
    
    啟動 Flask 營運伺服器
    """
    log.info("啟動 FamilyTree 操作伺服器...")
    # app.run(host='0.0.0.0', port=5555, use_reloader=False)
    app.run(port=5555, debug=True, use_reloader=True)

if __name__ == "__main__":
    main()
