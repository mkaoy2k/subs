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
from db_utils import add_subscriber, get_articles, remove_subscriber, verify_token, get_subscribers, get_articles_byDays
from email_utils import validate_email, generate_verification_token, send_verification_email, send_newsletter
from funcUtils import load_menu, load_L10N
import subprocess
from dotenv import load_dotenv  # 安裝: pip install python-dotenv
import logging

# 全局變數
g_L10N = {}
g_L10N_options = []
g_loc_key = None
g_loc = None
g_MENU = {}
g_menu = {}
g_PAGE = {}
g_home = {}
g_faq = {}
g_about = {}
backend = None
ft_svr = None
git_ftpe = None
git_subs = None

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

# 在 Flask 應用初始化後添加
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')  # 請在生產環境中設置安全的密鑰

# 在 465 端口上配置帶有 SSL 的 Flask-Mail
app.config.update(
    # 保持現有的郵件配置不變
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'mkaoy2k@gmail.com'),
    MAIL_DEBUG=0,
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
    """
    global g_L10N, g_L10N_options, g_loc_key, g_loc
    global g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about
    global backend, ft_svr, git_ftpe, git_subs
    
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
    g_menu = g_MENU[g_loc_key]
    
    # 初始化所有語言的頁面內容
    g_PAGE = {}
    for idx, loc in enumerate(g_L10N_options):
        l_page = {}
        l_loc = g_L10N[loc]
        
        # 初始化 home page from here
        cats = ["News", "Story", "Events"]
        l_home = {"News": [], "Story": [], "Events": []}
        for cat in cats:
            # get articles from last 7 days
            articles = get_articles_byDays(cat, byDays=7)
            log.debug(f"Found {len(articles)} articles in category '{cat}' from last 7 days")
            l_home[cat] = []
            for article in articles:
                if article['l10n'] == loc:
                    l_home[cat].append(article)
        l_page['home'] = l_home
        
        # 初始化 faq page from here
        cats = ["FAQ"]
        l_faq = {"FAQ": []}
        for cat in cats:
            # get all articles of this category
            articles = get_articles(cat)
            log.debug(f"Found {len(articles)} articles in category '{cat}'")
            for article in articles:
                if article['l10n'] == loc:
                    l_faq[cat].append(article)
        l_page['faq'] = l_faq
        
        # 初始化 about page from here
        cats = ["About"]
        l_about = {"About": []}
        for cat in cats:
            # get all articles of this category
            articles = get_articles(cat)
            log.debug(f"Found {len(articles)} articles in category '{cat}'")
            for article in articles:
                if article['l10n'] == loc:
                    l_about[cat].append(article)
        l_page['about'] = l_about
        
        # 將頁面內容添加到全局頁面字典中
        g_PAGE[idx] = l_page
    
    # 設定當前語言的頁面內容
    key = g_L10N_options.index(g_loc_key)
    g_home = g_PAGE[key]['home']
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    
    return (backend, ft_svr, git_ftpe, git_subs, g_L10N, g_L10N_options,
            g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about)
    
def get_template_context():
    """返回所有視圖函數共用的模板上下文"""
    return {
        'menu': g_menu,
        'options': g_L10N_options,
        'settings': g_loc['SETTINGS'],
        'your_language': g_loc['YOUR_LANGUAGE'],
        'subscribe': g_loc['SUBSCRIBE'],
        'unsubscribe': g_loc['UNSUBSCRIBE'],
        'email_subscription': g_loc['EMAIL_SUBSCRIPTION'],
        'motto_btn': g_loc['HOME_HTML_H2'],
        'motto': g_loc['HOME_HTML_MOTTO'],
        'current_lang': g_loc_key  # 使用全局變數而不是 session
    }    
@app.before_request
def before_request():
    """在每個請求之前執行"""
    global g_loc_key, g_loc, g_menu, g_home, g_faq, g_about
    
    # 確保 session 中有 current_lang
    if 'current_lang' not in session:
        session['current_lang'] = g_loc_key
    else:
        # 確保全局變數與 session 中的語言一致
        if session['current_lang'] != g_loc_key and session['current_lang'] in g_L10N_options:
            try:
                g_loc_key = session['current_lang']
                g_loc = g_L10N[g_loc_key]
                g_menu = g_MENU[g_loc_key]
                
                # 更新頁面內容
                key = g_L10N_options.index(g_loc_key)
                g_home = g_PAGE[key]['home']
                g_faq = g_PAGE[key]['faq']
                g_about = g_PAGE[key]['about']
            except Exception as e:
                log.error(f"更新語言時出錯: {str(e)}")
                
@app.route("/")
def home():
    """首頁路由"""
    context = get_template_context()
    t1 = g_loc['HOME_HTML_T1']
    t2 = g_loc['HOME_HTML_T2']
    t3 = g_loc['HOME_HTML_T3']
    
    context.update({
        'header': g_loc['HOME_HTML_H1'],
        't1': t1,
        't1_articles': g_home["News"],
        't2': t2,
        't2_title': g_home["Story"][0]['title'],
        't2_content': g_home["Story"][0]['content'],
        't2_image': g_home["Story"][0].get('image_url', ''),
        't2_image_alt': g_home["Story"][0].get('image_alt', ''),
        't3': t3,
        't3_article': g_home["Events"],
        't4_greeting': g_loc['HOME_HTML_T4_GREETING'],
        't4_team': g_loc['HOME_HTML_T4_TEAM'],
        'ft_url': ft_svr,
        'title': 'home'
    })
    return render_template('home.html', **context)

@app.route("/faq")
def faq():
    """常見問題頁面"""
    global g_faq
    if len(g_faq['FAQ']) < 5:
        log.debug(f"FAQ page content is not as planned: {g_faq['FAQ']}")
        flash(f"FAQ page content is not as planned: {g_faq['FAQ']}", 'error')
        return redirect(url_for('home'))
    context = get_template_context()
    context.update({
        'header': g_loc['FAQ_HTML_H1'],
        'questions': [article['title'] for article in g_faq["FAQ"]],
        'answers': [article['content'] for article in g_faq["FAQ"]],
        'authors': [article['author'] for article in g_faq["FAQ"]],
        'images': [article['src_url'] for article in g_faq["FAQ"]],
        'ft_url': ft_svr,
        'title': 'faq'
    })
    return render_template('faq.html', **context)

@app.route("/about")
def about():
    """關於頁面"""
    global g_about
    if len(g_about['About']) < 2:
        log.debug(f"About page content is not as planned: {g_about['About']}")
        flash(f"About page content is not as planned: {g_about['About']}", 'error')
        return redirect(url_for('home'))
    context = get_template_context()
    body = [None, None]
    log.debug(f"Processing about page content. Found {len(g_about['About'])} articles")
    
    # Log all article titles for debugging
    for article in g_about['About']:
        log.debug(f"Article title: '{article['title']}' (length: {len(article['content'])} chars)")
    
    # Match articles to expected sections
    for article in g_about['About']:
        if article['title'] == g_loc['ABOUT_INTRODUCTION_H2']:
            body[0] = article['content']
            log.debug(f"Found introduction article. Content length: {len(body[0])} chars")
        elif article['title'] == g_loc['ABOUT_REPOSITORY_H2']:
            body[1] = article['content']
            log.debug(f"Found repository article. Content length: {len(body[1])} chars")
    context.update({
        'header': g_loc['ABOUT_HTML_H1'],
        'introduction': g_loc['ABOUT_INTRODUCTION_H2'],
        'repository': g_loc['ABOUT_REPOSITORY_H2'],
        'body': body,
        'git_ftpe': git_ftpe,
        'git_subs': git_subs,
        'title': 'about'
    })
    return render_template('about.html', **context)

@app.route("/setL10N")
def set_l10n():
    """
    設置語言本地化 (L10N) 路由
    """
    global g_loc_key, g_loc, g_menu, g_faq, g_about, g_home
    
    # 從 URL 參數獲取語言和頁面
    lang = request.args.get('lang')
    page = request.args.get('page', 'home')
    
    if lang in g_L10N_options:
        try:
            # 更新全局變數
            g_loc_key = lang
            g_loc = g_L10N[lang]
            g_menu = g_MENU[lang]
            
            # 更新頁面內容
            key = g_L10N_options.index(lang)
            g_faq = g_PAGE[key]['faq']
            g_about = g_PAGE[key]['about']
            g_home = g_PAGE[key]['home']
            
            # 保存到 session
            session['current_lang'] = lang
            
        except Exception as e:
            log.error(f"語言切換錯誤: {str(e)}")
    
    # 重定向到目標頁面
    if page == "about":
        return redirect(url_for('about'))
    elif page == "faq":
        return redirect(url_for('faq'))
    return redirect(url_for('home'))

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

# ---- Admin tools below ----
@app.route('/usrq')
def user_query():
    """通過運行 ops_user_query.py 作為子進程執行數據庫查詢。
    
    返回：
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

@app.route('/usru')
def user_update():
    """通過運行 ops_user_update.py 作為子進程執行數據庫更新。
    
    返回：
        Response: 包含更新結果或錯誤訊息的 JSON 回應
    """
    import subprocess
    import json
    import os
    
    try:
        # 獲取當前腳本所在目錄
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'ops_user_update.py')
        
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

    context = get_template_context()
    t1 = g_loc['HOME_HTML_T1']
    t2 = g_loc['HOME_HTML_T2']
    t3 = g_loc['HOME_HTML_T3']
    
    context.update({
        'header': g_loc['HOME_HTML_H1'],
        't1': t1,
        't1_articles': g_home["News"],
        't2': t2,
        't2_title': g_home["Story"][0]['title'],
        't2_content': g_home["Story"][0]['content'],
        't2_image': g_home["Story"][0].get('image_url', ''),
        't2_image_alt': g_home["Story"][0].get('image_alt', ''),
        't3': t3,
        't3_articles': g_home["Events"],
        't4_greeting': g_loc['HOME_HTML_T4_GREETING'],
        't4_team': g_loc['HOME_HTML_T4_TEAM'],
        'ft_url': ft_svr,
        'title': g_loc['HOME_HTML_H1']
        })
    
    try:
        if send_newsletter(mail, emails, context):
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

# 初始化全局變數
init_globals()

if __name__ == "__main__":
    main()
