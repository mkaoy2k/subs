"""
FamilyTrees Operations Server

This module provides backend services for the FamilyTrees website, including user activation,
Frequently Asked Questions (FAQ), and About page with multi-language support.

Main Features:
- User account activation
- Multi-language support (L10N)
- FAQ page
- About page

Method 1: Direct Execution
python ops_svr.py

Method 2: Using Flask Command
flask --app ops_svr run -p 5555
"""

from flask import Flask, request, redirect, render_template, flash, url_for, session, jsonify
from flask_mail import Mail
import os
from dotenv import load_dotenv
import db_utils as dbm
from email_utils import validate_email, generate_verification_token, send_verification_email, send_newsletter
from funcUtils import load_menu, load_L10N
import logging

# Global variables
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

# Load environment variables
load_dotenv(".env")

# Configure logging
log = logging.getLogger(__name__)
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

# Remove existing handlers to avoid duplication
log.handlers = []

# Configure console handler format
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
log.addHandler(console_handler)

# Prevent propagation to root logger
log.propagate = False

# Add after Flask app initialization
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')  # Set a secure key in production environment

# Configure Flask-Mail with SSL on port 465
app.config.update(
    # Keep existing mail configuration unchanged
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

# Initialize Flask-Mail
mail = Mail(app)

# Test email configuration
log.info(f"Email server configured: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
log.info(f"Using TLS: {app.config['MAIL_USE_TLS']}, Using SSL: {app.config['MAIL_USE_SSL']}")

def init_globals():
    """
    Initialize global variables
    """
    global g_L10N, g_L10N_options, g_loc_key, g_loc
    global g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about
    global backend, ft_svr, git_ftpe, git_subs
    
    # Load database backend settings
    backend = os.getenv("DB_SVR", "sqlite3")
    log.debug(f"DB_SVR import: {backend}")
    
    # Set FamilyTrees server endpoints
    ft_svr = os.getenv("FT_SVR", "https://crappie-on-kingfish.ngrok-free.app")
    log.debug(f"FamilyTreesPE Server: {ft_svr}")    
    git_ftpe = os.getenv("GIT_FTPE", "https://github.com/mkaoy2k/ftpe.git")
    log.debug(f"ftpe GitHub Server: {git_ftpe}")
    git_subs = os.getenv("GIT_SUBS", "https://github.com/mkaoy2k/subs.git")
    log.debug(f"subs GitHub Server: {git_subs}")
    
    # Load multi-language support
    l10n_file = os.getenv("L10N_FILE")    
    g_L10N = load_L10N(l10n_file)
    g_L10N_options = list(g_L10N.keys())
    
    # Initialize system language settings
    g_loc_key = os.getenv("L10N")
    g_loc = g_L10N[g_loc_key]
    log.debug(f"L10N='{g_loc_key}'...")
    
    # Load Application settings
    article_window = int(os.getenv("ARTICLE_WINDOW", "7"))
    log.debug(f"ARTICLE_WINDOW: {article_window}")
    
    # Load menu
    f_menu = os.getenv("OPS_MENU_FILE")
    g_MENU = load_menu(f_menu)
    g_menu = g_MENU[g_loc_key]
    
    # Initialize page content for all languages
    g_PAGE = {}
    for idx, loc in enumerate(g_L10N_options):
        l_page = {}
        l_loc = g_L10N[loc]
        
        # Initialize home page from here
        cats = ["News", "Story", "Events"]
        l_home = {"News": [], "Story": [], "Events": []}
        for cat in cats:
            # get articles within the window
            articles = dbm.get_articles_byDays(cat, byDays=article_window)
            log.debug(f"Found {len(articles)} articles in category '{cat}' from last {article_window} days")
            l_home[cat] = []
            for article in articles:
                if article['l10n'] == loc:
                    l_home[cat].append(article)
        l_page['home'] = l_home
        
        # Initialize FAQ page from here
        cats = ["FAQ"]
        l_faq = {"FAQ": []}
        for cat in cats:
            # get all articles of this category
            articles = dbm.get_articles(cat)
            log.debug(f"Found {len(articles)} articles in category '{cat}'")
            for article in articles:
                if article['l10n'] == loc:
                    l_faq[cat].append(article)
        l_page['faq'] = l_faq
        
        # Initialize about page from here
        cats = ["About"]
        l_about = {"About": []}
        for cat in cats:
            # get all articles of this category
            articles = dbm.get_articles(cat)
            log.debug(f"Found {len(articles)} articles in category '{cat}'")
            for article in articles:
                if article['l10n'] == loc:
                    l_about[cat].append(article)
        l_page['about'] = l_about
        
        # Add page content to global page dictionary
        g_PAGE[idx] = l_page
    
    # Set page content for current language
    key = g_L10N_options.index(g_loc_key)
    g_home = g_PAGE[key]['home']
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    
    return (backend, ft_svr, git_ftpe, git_subs, g_L10N, g_L10N_options,
            g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, g_home, g_faq, g_about)
    
def get_template_context():
    """Return template context for all view functions"""
    return {
        'menu': g_menu,
        'options': g_L10N_options,
        'release': g_loc['RELEASE'],
        'settings': g_loc['SETTINGS'],
        'your_language': g_loc['YOUR_LANGUAGE'],
        'subscribe': g_loc['SUBSCRIBE'],
        'unsubscribe': g_loc['UNSUBSCRIBE'],
        'email_subscription': g_loc['EMAIL_SUBSCRIPTION'],
        'motto_btn': g_loc['HOME_HTML_H2'],
        'motto': g_loc['HOME_HTML_MOTTO'],
        'current_lang': g_loc_key  # Use global variable instead of session
    }    
@app.before_request
def before_request():
    """Execute before each request"""
    global g_loc_key, g_loc, g_menu, g_home, g_faq, g_about
    
    # Ensure current_lang exists in session
    if 'current_lang' not in session:
        session['current_lang'] = g_loc_key
    else:
        # Ensure global variable matches language in session
        if session['current_lang'] != g_loc_key and session['current_lang'] in g_L10N_options:
            try:
                g_loc_key = session['current_lang']
                g_loc = g_L10N[g_loc_key]
                g_menu = g_MENU[g_loc_key]
                
                # Update page content
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
    
    # 檢查 Story 是否有內容，如果沒有則使用預設值
    story_data = {
        't2_title': g_loc['HOME_HTML_NO_STORY_TITLE'],
        't2_content': g_loc['HOME_HTML_NO_STORY_CONTENT'],
        't2_image': '',
        't2_image_alt': ''
    }
    
    if g_home["Story"] and len(g_home["Story"]) > 0:
        story_data = {
            't2_title': g_home["Story"][0].get('title', g_loc['HOME_HTML_NO_STORY_TITLE']),
            't2_content': g_home["Story"][0].get('content', g_loc['HOME_HTML_NO_STORY_CONTENT']),
            't2_image': g_home["Story"][0].get('image_url', ''),
            't2_image_alt': g_home["Story"][0].get('image_alt', '')
        }
    
    context.update({
        'release': g_loc['RELEASE'],
        'header': g_loc['HOME_HTML_H1'],
        't1': t1,
        't1_articles': g_home.get("News", []),
        'author_label': g_loc['HTML_AUTHOR_LABEL'],
        'source_label': g_loc['HTML_SOURCE_LABEL'],
        't2': t2,
        't2_title': story_data['t2_title'],
        't2_content': story_data['t2_content'],
        't2_image': story_data['t2_image'],
        't2_image_alt': story_data['t2_image_alt'],
        't3': t3,
        't3_article': g_home.get("Events", []),
        't4_greeting': g_loc['HOME_HTML_T4_GREETING'],
        't4_team': g_loc['HOME_HTML_T4_TEAM'],
        'ft_url': ft_svr,
        'title': 'home'
    })
    return render_template('home.html', **context)

@app.route("/faq")
def faq():
    """FAQ page"""
    global g_faq
    if len(g_faq['FAQ']) < 5:
        log.debug(f"FAQ page content is not as planned: {g_faq['FAQ']}")
        flash(f"FAQ page content is not as planned: {g_faq['FAQ']}", 'error')
        return redirect(url_for('home'))
    context = get_template_context()
    context.update({
        'release': g_loc['RELEASE'],
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
    """About page"""
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
        'release': g_loc['RELEASE'],
        'header': g_loc['ABOUT_HTML_H1'],
        'introduction': g_loc['ABOUT_INTRODUCTION_H2'],
        'repository': g_loc['ABOUT_REPOSITORY_H2'],
        'body': body,
        'git_ftpe': git_ftpe,
        'git_subs': git_subs,
        'title': 'about'
    })
    return render_template('about.html', **context)

@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    """
    Feedback page for article submission
    """
    from forms import ArticleForm
    
    context = get_template_context()
    lang = session.get('current_lang', 'US')
    
    # Initialize form with current language
    form = ArticleForm(lang=lang)
    
    if form.validate_on_submit():
        # Process the form data
        title = form.title.data
        content = form.content.data
        category = form.category.data
        l10n = form.l10n.data
        author = form.author.data
        source = form.source.data
        src_url = form.source_url.data or None
        image_url = form.image_url.data or None
        email = form.email.data
        if not validate_email(email):
            log.warning(f"Invalid email address: {email}")
            flash(f'{g_loc.get("EMAIL_INVALID", "Invalid email address")}', 'danger')
            return redirect(request.referrer or url_for('home'))
        
        # Check if user is a subscriber, if not add them as pending
        subscriber = dbm.get_subscriber(email)
        if not subscriber:
            log.info(f"New subscriber detected: {email}, adding to pending")
            if not dbm.add_subscriber(email, 'pending_verification', lang=lang):
                log.error(f"Failed to add new subscriber: {email}")
                flash(f'{g_loc.get("ADD_SUB_ERROR", "Subscriber not created/updated. Please subscribe again later.")}', 'danger')
                return redirect(request.referrer or url_for('home'))
            flash(f'{g_loc.get("EMAIL_SUB_NEEDED", "Please subscribe with your email before submitting articles.")}', 'danger')
            return redirect(url_for('feedback'))
        elif subscriber.get('is_active') != dbm.Subscriber_State['active']:  # Check if subscriber is not active
            log.warning(f"Non-active subscriber attempted submission: {email}")
            flash(f'{g_loc.get("EMAIL_CONFIRM_NEEDED", "Please confirm your email {email} before submitting content.")}', 'danger')
            return redirect(url_for('feedback'))
        log.debug(f"Article form data: {form.data}")
        log.debug(f"Article form errors: {form.errors}")
        
        # Create the article in the database
        article_id = dbm.create_article(
            title=title,
            content=content,
            category=category,
            author=author,
            source=source,
            src_url=src_url,
            image_url=image_url,
            l10n=l10n
        )
        
        if article_id:
            log.debug(f"Successfully created article with ID: {article_id}")
            flash(f'{g_loc.get("ARTICLE_SUCCESS", "Submitted successfully")}', 'success')            # Redirect to home page after successful submission
            return redirect(url_for('home'))
        else:
            log.debug(f"Failed to create article")
            flash(f'{g_loc.get("ARTICLE_RETRY", "Article not created. Please re-submit later.")}', 'danger')
    
    # Get template context for rendering
    context.update({
        'header': g_loc.get('FEEDBACK_HTML_H1', 'Submit Feedback'),
        'title': 'feedback',
        'form': form,
    })
    
    return render_template('feedback.html', **context)

@app.route("/setL10N")
def set_l10n():
    """
    Set up language localization (L10N) routing
    """
    global g_loc_key, g_loc, g_menu, g_faq, g_about, g_home
    
    # Get language and page from URL parameters
    lang = request.args.get('lang')
    page = request.args.get('page', 'home')
    
    if lang in g_L10N_options:
        try:
            # reload global variables
            init_globals()
            # Update global variables
            g_loc_key = lang
            g_loc = g_L10N[lang]
            g_menu = g_MENU[lang]
            
            # Update page content
            key = g_L10N_options.index(lang)
            g_faq = g_PAGE[key]['faq']
            g_about = g_PAGE[key]['about']
            g_home = g_PAGE[key]['home']
            
            # Save to session
            session['current_lang'] = lang
            
        except Exception as e:
            log.error(f"Language switch error: {str(e)}")
    
    # Redirect to target page
    if page == "feedback":
        return redirect(url_for('feedback'))
    elif page == "about":
        return redirect(url_for('about'))
    elif page == "faq":
        return redirect(url_for('faq'))
    return redirect(url_for('home'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """
    Handle email subscription/unsubscription request
    
    Returns:
        Response: Redirect back to previous page and display operation result
    """
    global g_loc_key
    
    email = request.form.get('email')
    action = request.form.get('action')
    
    if not validate_email(email):
        flash(f'{email} is not a valid email address', 'danger')
        return redirect(request.referrer or url_for('home'))
    
    try:
        if action == 'subscribe':
            # Generate verification token
            token = generate_verification_token()
            # Send verification email
            if send_verification_email(mail, email, token, is_subscribe=True):
                if dbm.add_subscriber(email, token, lang=g_loc_key):
                    log.debug(f"Subscribed {email} with lang={g_loc_key}")
                    flash(f'Please check {email} to confirm subscription.', 'info')
                else:
                    flash(f'Failed to subscribe {email}. Please try again later.', 'danger')
            else:
                flash('Failed to send verification email. Please try again later.', 'danger')
        else:
            # For unsubscribing, we can send a verification email or unsubscribe directly
            # For security, we send a verification email here
            token = generate_verification_token()
            if send_verification_email(mail, email, token, is_subscribe=False):
                flash(f'Please check {email} to confirm unsubscription.', 'info')
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
    global g_loc_key
    
    email = request.args.get('email')
    token = request.args.get('token')
    action = request.args.get('action')
    
    if not all([email, token, action]):
        log.debug(f"Invalid verification link: {email}, {token}, {action}")
        flash('Invalid verification link', 'danger')
        return redirect(url_for('home'))
    
    # Verify token
    if not verify_token(email, token):
        log.debug(f"Invalid or expired verification link: {email}, {token}, {action}")
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('home'))
    
    # Handle subscription/unsubscription
    if action == 'subscribe':
        if dbm.add_subscriber(email, token):
            log.debug(f"Subscribed {email} with lang={g_loc_key}")
            flash(f'{email} has been successfully subscribed to our newsletter!', 'success')
        else:
            flash(f'Failed to subscribe {email}. Please try again later.', 'danger')
    else:
        dbm.remove_subscriber(email)
        flash(f'{email} has been unsubscribed from our newsletter.', 'info')
    
    return redirect(url_for('home'))

# ---- Admin tools below ----

@app.route('/pub')
def pub_newsletter():
    """
    retrieve active subscribers' emails from db and send newsletter
    """
    global g_loc, g_home, g_loc_key
    lang = request.args.get('lang', g_loc_key)
    if lang not in g_L10N_options:
        lang = g_loc_key
        
    # reload global variables
    init_globals()
    # Update global variables
    g_loc_key = lang
    g_loc = g_L10N[lang]
            
    # Update page content
    key = g_L10N_options.index(lang)
            
    # Save to session
    session['current_lang'] = lang
    users = dbm.get_subscribers(state='active', lang=lang)
    if not users:  # Handles both None and empty list
        log.debug(f"No active subscribers found for language: {lang}")
        flash(f'{g_loc.get("NO_ACTIVE_SUBSCRIBERS", "No active subscribers found")}', 'warning')
        return redirect(url_for('home'))
        
    emails = [user['email'] for user in users if user and 'email' in user]
    if not emails:  
        # In case all users in the list are invalid or missing email
        log.debug(f"No valid emails found for language: {lang}")
        flash(f'{g_loc.get("NO_EMAILS_FOUND", "No valid emails found")}', 'danger')
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
            log.debug(f"Newsletter sent successfully for language: {lang}")
            flash(f'{g_loc.get("PUB_HTML_SUCCESS", "Newsletter sent successfully.")}', 'success')
        else:
            log.debug(f"Newsletter sent failed for language: {lang}")
            flash(f'{g_loc.get("PUB_HTML_FAIL", "Newsletter sent failed, please try later")}', 'danger')
    except Exception as e:
        log.debug(f"Newsletter sent failed for language: {lang}")
        flash(f'{g_loc.get("PUB_HTML_FAIL", "Newsletter sent failed.")}', 'danger')
    return redirect(url_for('home'))    

def main():
    """
    Main function
    
    Start Flask server
    """
    log.info("Starting FamilyTreesOps server...")
    app.run(host='0.0.0.0', port=5555, use_reloader=False)
    # app.run(port=5555, debug=True, use_reloader=True)

# Initialize global variables
init_globals()

if __name__ == "__main__":
    main()
