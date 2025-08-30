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

from flask import Flask, request, redirect, render_template, flash, url_for, session, jsonify, abort
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from flask_mail import Mail
import os
import email_utils as eu
import auth_utils as au
import db_utils as dbm
from funcUtils import load_menu, load_L10N, load_page_cat
import logging
from dotenv import load_dotenv

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
app = Flask(__name__, template_folder='templates')
# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token expiration
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['REMEMBER_COOKIE_SECURE'] = True  # Only send remember cookies over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent client-side JS access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection for same-site requests

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Make CSRF token available in all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

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
g_fmail = Mail(app)

# Test email configuration
log.info(f"Email server configured: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
log.info(f"Using TLS: {app.config['MAIL_USE_TLS']}, Using SSL: {app.config['MAIL_USE_SSL']}")

def init_globals():
    """
    Initialize global variables
    """
    global g_L10N, g_L10N_options, g_loc_key, g_loc
    global g_MENU, g_menu, g_PAGE, g_PAGE_CAT, g_home, g_faq, g_about
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
    g_L10N = load_L10N()
    g_L10N_options = list(g_L10N.keys())
    
    # Initialize system language settings
    g_loc_key = os.getenv("L10N")
    g_loc = g_L10N[g_loc_key]
    log.debug(f"L10N='{g_loc_key}'...")
    
    # Load Application settings
    article_window = int(os.getenv("ARTICLE_WINDOW", "7"))
    log.debug(f"ARTICLE_WINDOW: {article_window}")
    
    # Load menu
    f_menu = os.getenv("OPS_MENU_FILE","ops_menu.json")
    g_MENU = load_menu(f_menu)
    g_menu = g_MENU[g_loc_key]
   
    # Load page categories
    f_page_cat = os.getenv("OPS_PAGE_CAT","page_category.json")
    g_PAGE_CAT = load_page_cat(f_page_cat)
    log.debug(f"Page categories: {g_PAGE_CAT}")
    
    # Initialize page content for all languages
    g_PAGE = {}
    for idx, loc in enumerate(g_L10N_options):
        l_page = {}
        
        # Initialize home page from here
        cats = g_PAGE_CAT['home']
        l_home = {}
        for cat in cats:
            # get articles within the window
            articles = dbm.get_articles_byDays(cat, byDays=article_window)
            if articles:
                log.debug(f"Found {len(articles)} articles in category '{cat}' from last {article_window} days")
                l_home[cat] = []
                for article in articles:
                    if article['l10n'] == loc:
                        l_home[cat].append(article)
            else:
                log.debug(f"No articles found in category '{cat}' from last {article_window} days")
        l_page['home'] = l_home
        
        # Initialize FAQ page from here
        cats = g_PAGE_CAT['faq']
        l_faq = {}
        for cat in cats:
            # get all articles of this category
            articles = dbm.get_articles(cat)
            if articles:
                log.debug(f"Found {len(articles)} articles in category '{cat}'")
                l_faq[cat] = []
                for article in articles:
                    if article['l10n'] == loc:
                        l_faq[cat].append(article)
            else:
                log.debug(f"No articles found in category '{cat}'")
        l_page['faq'] = l_faq
        
        # Initialize about page from here
        cats = g_PAGE_CAT['about']
        l_about = {}
        for cat in cats:
            # get all articles of this category
            articles = dbm.get_articles(cat)
            if articles:
                log.debug(f"Found {len(articles)} articles in category '{cat}'")
                l_about[cat] = []
                for article in articles:
                    if article['l10n'] == loc:
                        l_about[cat].append(article)
            else:
                log.debug(f"No articles found in category '{cat}'")
        l_page['about'] = l_about
        
        # Add page content to global page dictionary
        g_PAGE[idx] = l_page
    
    # Set page content for current language
    key = g_L10N_options.index(g_loc_key)
    g_home = g_PAGE[key]['home']
    g_faq = g_PAGE[key]['faq']
    g_about = g_PAGE[key]['about']
    
    return (backend, ft_svr, git_ftpe, git_subs, g_L10N, g_L10N_options,
            g_loc_key, g_loc, g_MENU, g_menu, g_PAGE, g_PAGE_CAT, g_home, g_faq, g_about)
    
def get_template_context():
    """Return template context for all view functions"""
    return {
        'menu': g_menu,
        'options': g_L10N_options,
        'release': os.getenv("RELEASE", ""),
        'settings': g_loc['SETTINGS'],
        'admin': g_loc['HOME_HTML_T4_TEAM'],
        'admin_email': os.getenv("DB_ADMIN", ""),
        'office_days': os.getenv("OFFICE_DAYS", "Monday - Friday"),
        'office_hours': os.getenv("OFFICE_HOURS", "9:00 AM - 5:00 PM (PST)"),
        'mailing_address': os.getenv("MAILING_ADDRESS", ""),
        'mailing_city': os.getenv("MAILING_CITY", ""),
        'mailing_country': os.getenv("MAILING_COUNTRY", ""),
        'your_language': g_loc['YOUR_LANGUAGE'],
        'subscribe': g_loc['SUBSCRIBE'],
        'unsubscribe': g_loc['UNSUBSCRIBE'],
        'email_subscription': g_loc['EMAIL_SUBSCRIPTION'],
        'motto_btn': g_loc['HOME_HTML_H2'],
        'motto': g_loc['HOME_HTML_MOTTO'],
        'ops_svr': os.getenv("OPS_SVR", "http://localhost:5566"),
        'current_lang': g_loc_key  # Use global variable instead of session
    }
    
@app.before_request
def before_request():
    """Execute before each request"""
    global g_loc_key, g_loc, g_menu, g_home, g_faq, g_about, g_PAGE
    
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
                log.error(f"Language switch error: {str(e)}")
                
@app.route("/")
def home():
    """Home page"""
    context = get_template_context()
    t1 = g_loc['HOME_HTML_T1']
    t2 = g_loc['HOME_HTML_T2']
    t3 = g_loc['HOME_HTML_T3']
    
    # Check if Story has content, if not use default values
    story_data = {
        't2_title': g_loc['HOME_HTML_NO_STORY_TITLE'],
        't2_content': g_loc['HOME_HTML_NO_STORY_CONTENT'],
        't2_image': '',
        't2_image_alt': '',
        't2_author': '',
        't2_src_url': '',
        't2_source': ''
    }
    
    try:
        if g_home["Story"] and len(g_home["Story"]) > 0:
            story_data = {
                't2_title': g_home["Story"][0].get('title', g_loc['HOME_HTML_NO_STORY_TITLE']),
                't2_content': g_home["Story"][0].get('content', g_loc['HOME_HTML_NO_STORY_CONTENT']),
                't2_image': g_home["Story"][0].get('image_url', ''),
                't2_image_alt': g_home["Story"][0].get('image_alt', ''),
                't2_author': g_home["Story"][0].get('author', ''),
                't2_src_url': g_home["Story"][0].get('src_url', ''),
                't2_source': g_home["Story"][0].get('source', '')
            }
    
    except Exception as e:
        log.warning(f"Skip processing story: {str(e)}")
    
    context.update({
        'release': os.getenv("RELEASE", ""),
        'header': g_loc['HOME_HTML_H1'],
        't1': t1,
        't1_articles': g_home.get("News") or [
            {
                'title': g_loc.get('HOME_HTML_NO_NEWS_TITLE', 'No News Available'),
                'content': g_loc.get('HOME_HTML_NO_NEWS_CONTENT', 'Check back later for updates.')
            }
        ],
        'author_label': g_loc['HTML_AUTHOR_LABEL'],
        'source_label': g_loc['HTML_SOURCE_LABEL'],
        't2': t2,
        't2_title': story_data['t2_title'],
        't2_content': story_data['t2_content'],
        't2_image': story_data['t2_image'],
        't2_image_alt': story_data['t2_image_alt'],
        't2_author': story_data['t2_author'],
        't2_src_url': story_data['t2_src_url'],
        't2_source': story_data['t2_source'],
        't3': t3,
        't3_article': g_home.get("Events") or [
            {
                'title': g_loc.get('HOME_HTML_NO_EVENT_TITLE', 'No Events Available'),
                'content': g_loc.get('HOME_HTML_NO_EVENT_CONTENT', 'Check back later for updates.')
            }
        ],
        't4_greeting': g_loc['HOME_HTML_T4_GREETING'],
        't4_team': g_loc['HOME_HTML_T4_TEAM'],
        'ft_url': ft_svr,
        'title': 'home'
    })
    return render_template('home.html', **context)

@app.route("/faq")
def faq():
    """FAQ page"""
    global g_loc, g_faq
    
    context = get_template_context()
    
    # Get the articles for the current language's FAQ category
    faq_articles = g_faq['FAQ']
    
    context.update({
        'release': os.getenv("RELEASE", ""),
        'header': g_loc['FAQ_HTML_H1'],
        'questions': [article['title'] for article in faq_articles],
        'answers': [article['content'] for article in faq_articles],
        'authors': [article['author'] for article in faq_articles],
        'images': [article['src_url'] for article in faq_articles],
        'ft_url': ft_svr,
        'title': 'faq'
    })
    return render_template('faq.html', **context)

@app.route("/about")
def about():
    """About page"""
    global g_loc, g_about, git_ftpe, git_subs
    
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
        'release': os.getenv("RELEASE", ""),
        'header': g_loc['ABOUT_HTML_H1'],
        'introduction': g_loc['ABOUT_INTRODUCTION_H2'],
        'repository': g_loc['ABOUT_REPOSITORY_H2'],
        'body': body,
        'git_ftpe': git_ftpe,
        'git_subs': git_subs,
        'title': 'about'
    })
    return render_template('about.html', **context)

@app.route("/privacy")
def privacy():
    """Privacy Policy page"""
    global g_loc
    
    context = get_template_context()
    context.update({
        'release': os.getenv("RELEASE", ""),
        'header': g_loc.get('PRIVACY_HEADER', 'Privacy Policy'),
        'title': 'privacy',
        'admin': context['admin'],
        'admin_email': context['admin_email'],
        'last_updated': '2024-06-26'
    })
    return render_template('privacy.html', **context)

@app.route("/terms")
def terms():
    """Terms of Service page"""
    global g_loc
    
    context = get_template_context()
    context.update({
        'release': os.getenv("RELEASE", ""),
        'header': g_loc.get('TERMS_HEADER', 'Terms of Service'),
        'title': 'terms',
        'admin': context['admin'],
        'admin_email': context['admin_email'],
        'last_updated': '2024-06-26'
    })
    return render_template('terms.html', **context)

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    from forms import ContactForm
    
    """Contact Us page"""
    global g_loc
    
    context = get_template_context()
    message_sent = False
    form = ContactForm()
    
    if form.validate_on_submit():
        # Get form data
        form_data = {
            'name': form.name.data.strip(),
            'email': form.email.data.strip(),
            'subject': form.subject.data.strip(),
            'message': form.message.data.strip()
        }
        
        # Check if user exists, if not create a new user
        user = dbm.get_subscriber(form_data['email'])
        if not user:
            user_id = dbm.create_user(form_data['email'], dbm.Subscriber_State['in_contact'], lang=context['current_lang'])
            if not user_id:
                flash(g_loc.get('ADD_CONTACT_ERROR', 'Contact not created/updated. Please try again later.'), 'danger')
                return redirect(url_for('contact'))
        else:
            user_id = user['id']
        # Save the form data to database
        article_data = {
            'title': form_data['subject'],
            'content': form_data['message'],
            'category': dbm.Article_Categories['contact'],
            'author': form_data['name'],
            'source': form_data['email'],
            'src_url': '',
            'image_url': '',
            'l10n': context['current_lang'],
            'user_id': user_id
        }
        article_id = dbm.add_or_update_article(article_data, 
                                        update=True)
            
        if article_id:
            log.info(f"Created contact form article successfully withID: {article_id}")
            # Send email to admin
            to_emails = [context.get('admin_email')]
            subject = f"New Contact Article: {article_id}"
            html = f"""
            <p>Subject: {form_data['subject']}</p>
            <p>Content: {form_data['message']}</p>
            <p>Author: {form_data['name']}</p>
            <p>Source: {form_data['email']}</p>
            """
            if eu.send_email(g_fmail, to_emails, subject, html):
                log.info(f"Successfully sent contact email to {to_emails}")
            else:
                log.error(f"Failed to send contact email to {to_emails}")
            message_sent = True
            flash(g_loc.get('CONTACT_SUCCESS', 'Your contact request has been sent. We will get back to you soon!'), 'success')
            return redirect(url_for('contact'))
        else:
            log.error("Failed to create contact form article")
            flash(g_loc.get('CONTACT_ERROR', 'Failed to send contact request. Please try again later.'), 'danger')
    
    # Initialize form_data with empty values if not set
    if 'form_data' not in locals():
        form_data = {
            'name': '',
            'email': '',
            'subject': '',
            'message': ''
        }
    
    # Add form data to context
    context.update({
        'form': form,
        'release': os.getenv("RELEASE", ""),
        'header': g_loc.get('CONTACT_HEADER', 'Contact Us'),
        'title': 'contact',
        'admin': context['admin'],
        'admin_email': context['admin_email'],
        'office_days': context['office_days'],
        'office_hours': context['office_hours'],
        'mailing_address': context['mailing_address'],
        'mailing_city': context['mailing_city'],
        'mailing_country': context['mailing_country'],
        'message_sent': message_sent,
        'form_labels': {
            'name': g_loc.get('CONTACT_NAME', 'Your Name'),
            'email': g_loc.get('CONTACT_EMAIL', 'Email Address'),
            'subject': g_loc.get('CONTACT_SUBJECT', 'Subject'),
            'message': g_loc.get('CONTACT_MESSAGE', 'Your Message'),
            'submit': g_loc.get('CONTACT_SUBMIT', 'Send Message')
        }
    })
    return render_template('contact.html', **context)

@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    """
    Feedback page for article submission
    """
    from forms import ArticleForm
    from werkzeug.datastructures import MultiDict
    
    context = get_template_context()
    lang = session.get('current_lang', 'US')
    
    # Initialize form based on request method
    if request.method == 'POST':
        log.debug(f"Form data received: {request.form}")
        
        # Create form with data from request using formdata
        form = ArticleForm(formdata=request.form, meta={'csrf': True}, lang=lang)
        
        # Manually populate the form data
        for field in form:
            if field.name in request.form:
                field.data = request.form[field.name]
        
        # Log form data before validation
        log.debug(f"Form data before validation: {form.data}")
        log.debug(f"Request form data: {dict(request.form)}")
        
        # Process the form data if validation passes
        if form.validate():
            log.debug("Form validation passed")
            log.debug(f"Form data after validation: {form.data}")
            
            # Process the form data
            title = form.title.data
            content = form.content.data
            l10n = form.l10n.data
            author = form.author.data
            source = form.source.data
            src_url = form.source_url.data or None
            image_url = form.image_url.data or None
            email = form.email.data
            
            # Validate email format
            if not eu.validate_email(email):
                log.warning(f"Invalid email address: {email}")
                flash(f'{g_loc.get("EMAIL_INVALID", "Invalid email address")}', 'danger')
            else:
                # Check if user is a subscriber, if not add them as pending
                subscriber = dbm.get_subscriber(email)
                if not subscriber:
                    log.info(f"New subscriber detected: {email}, adding to pending")
                    user_data = {
                        'email': email,
                        'is_active': dbm.Subscriber_State['pending'],
                        'token': 'pending_verification',
                        'l10n': lang
                    }
                    if not dbm.add_or_update_subscriber(user_data):
                        log.error(f"Failed to add new subscriber: {email}")
                        flash(f'{g_loc.get("ADD_SUB_ERROR", "Subscriber not created/updated. Please try again later.")}', 'danger')
                    else:
                        flash(f'{g_loc.get("EMAIL_SUB_NEEDED", "Please check your email to confirm your subscription before submitting articles.")}', 'warning')
                elif subscriber.get('is_active') != dbm.Subscriber_State['active']:  # Check if subscriber is not active
                    log.warning(f"Non-active subscriber attempted submission: {email}")
                    flash(f'{g_loc.get("EMAIL_CONFIRM_NEEDED", f"Please confirm your email {email} before submitting content.")}', 'warning')
                else:
                    # Only proceed with article creation if all validations pass
                    try:
                        # Create the article in the database
                        article_data = {
                            'title': title,
                            'content': content,
                            'category': dbm.Article_Categories['feedback'],
                            'author': author,
                            'source': source,
                            'src_url': src_url,
                            'image_url': image_url,
                            'user_id': subscriber['id'],
                            'l10n': l10n
                        }
                        
                        article_id = dbm.add_or_update_article(article_data, 
                                        update=True)
                        
                        if article_id:
                            log.debug(f"Successfully created article with ID: {article_id}")
                            
                            # Send email to admin
                            to_emails = [context.get('admin_email')]
                            subject = f"New Feedback Article: {article_id}"
                            html = f"""
                            <p>Subject: {title}</p>
                            <p>Content: {content}</p>
                            <p>Author: {author}</p>
                            <p>Source: {source}</p>
                            <p>Source URL: {src_url}</p>
                            <p>Image URL: {image_url}</p>
                            """
                            if eu.send_email(g_fmail, 
                                to_emails, 
                                subject, html):
                                log.info(f"Successfully sent feedback email to {to_emails}")
                            else:
                                log.error(f"Failed to send feedback email to {to_emails}")
                            
                            flash(f'Ticket:{article_id}, {g_loc.get("FEEDBACK_SUCCESS", "Submitted successfully")}', 'success')
                            # Redirect to home page after successful submission
                            return redirect(url_for('home'))
                        else:
                            log.error("Failed to create article in database")
                            flash(f'{g_loc.get("FEEDBACK_RETRY", "Article not created. Please try again later.")}', 'danger')
                    except Exception as e:
                        log.error(f"Error creating article: {str(e)}")
                        flash(f'{g_loc.get("FEEDBACK_ERROR", "An error occurred. Please try again.")}', 'danger')
        else:
            log.warning(f"Form validation failed: {form.errors}")
            # Log each field's error for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    log.warning(f"Field '{field}': {error}")
    else:
        # Initialize empty form for GET request
        form = ArticleForm(meta={'csrf': True}, lang=lang)
    
    # Update context with form data
    context.update({
        'header': g_loc.get('FEEDBACK_HTML_H1', 'Submit Feedback'),
        'title': 'feedback',
        'form': form,
    })
    
    # Log form state before rendering
    log.debug(f"Form data before render: {form.data}")
    log.debug(f"Form errors before render: {form.errors}")
    log.debug(f"Form is bound: {form.is_submitted()}")
    log.debug(f"Form validate on submit: {form.validate_on_submit()}")
    log.debug(f"CSRF Token: {form.csrf_token.current_token if hasattr(form, 'csrf_token') else 'No CSRF token'}")
    
    # Debug: Log all form fields and their data
    log.debug("=== Form Field Values ===")
    for field_name, field in form._fields.items():
        log.debug(f"Field: {field_name}, Type: {type(field).__name__}, Data: {field.data}, Raw Data: {field.raw_data}, Errors: {field.errors}")
    log.debug("=======================")
    
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
# 前端表單中必須包含: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
def subscribe():
    """
    Handle email subscription/unsubscription request
    
    Returns:
        Response: Redirect back to previous page and display operation result
    """
    global g_loc_key
    
    # CSRF protection is automatically handled by Flask-WTF
    
    email = request.form.get('email')
    action = request.form.get('action')
    
    if not eu.validate_email(email):
        flash(f'{email} is not a valid email address', 'danger')
        return redirect(request.referrer or url_for('home'))
    
    try:
        if action == 'subscribe':
            # Generate verification token
            token = eu.generate_verification_token()
            # Send verification email
            if eu.send_verification_email(g_fmail, email, token, is_subscribe=True):
                user_data = {
                    'email': email,
                    'is_active': dbm.Subscriber_State['pending'],
                    'token': token,
                    'l10n': g_loc_key
                }
                if dbm.add_or_update_subscriber(user_data):
                    log.debug(f"Subscribed {email} with lang={g_loc_key}")
                    flash(f'Please check {email} to confirm subscription.', 'info')
                else:
                    flash(f'Failed to subscribe {email}. Please try again later.', 'danger')
            else:
                flash('Failed to send verification email. Please try again later.', 'danger')
        else:
            # For unsubscribing, we can send a verification email or unsubscribe directly
            # For security, we send a verification email here
            token = eu.generate_verification_token()
            if eu.send_verification_email(g_fmail, email, token, is_subscribe=False):
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
    if not dbm.verify_token(email, token):
        log.debug(f"Invalid or expired verification link: {email}, {token}, {action}")
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('home'))
    
    # Handle subscription/unsubscription
    if action == 'subscribe':
        user_data = {
            'email': email,
            'is_active': dbm.Subscriber_State['active'],
            'token': token,
            'l10n': g_loc_key
        }
        if dbm.add_or_update_subscriber(user_data):
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
    global g_loc, g_home, g_loc_key, g_L10N, g_L10N_options
    
    lang = request.args.get('lang', g_loc_key)
    email = request.args.get('email')
    password = request.args.get('password')
    
    if lang not in g_L10N_options:
        log.debug(f"Language not found: {lang}")
        flash(f'{g_loc.get("PUB_HTML_FAILS", "Language not found")}', 'warning')
        return redirect(url_for('home'))   
    
    # Show login page and check if user is admin     
    if not au.verify_admin(email, password):
        log.debug(f"Login failed")
        flash(f'{g_loc.get("LOGIN", "login")} {g_loc.get("FAILED", "failed")}', 'warning')
        return redirect(url_for('login'))
    
    # reload global variables
    init_globals()
    # Update global variables
    g_loc_key = lang
    g_loc = g_L10N[lang]
            
    # Update page content
    key = g_L10N_options.index(lang)
    g_home = g_PAGE[key]['home']
    
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
    
    # Prepare story data with safe defaults
    story_data = {
        't2_title': g_loc.get('HOME_HTML_NO_STORY_TITLE', 'Featured Story'),
        't2_content': g_loc.get('HOME_HTML_NO_STORY_CONTENT', 'No story content available'),
        't2_image': '',
        't2_image_alt': '',
        't2_author': '',
        't2_source': '',
        't2_src_url': ''
    }
    
    # Update story data if available
    if 'Story' in g_home and isinstance(g_home['Story'], list) and len(g_home['Story']) > 0:
        story = g_home['Story'][0]
        story_data.update({
            't2_title': story.get('title', story_data['t2_title']),
            't2_content': story.get('content', story_data['t2_content']),
            't2_image': story.get('image_url', ''),
            't2_image_alt': story.get('image_alt', ''),
            't2_author': story.get('author', ''),
            't2_source': story.get('source', ''),
            't2_src_url': story.get('src_url', '')
        })
    
    # Prepare context with safe dictionary access
    context.update({
        'header': g_loc.get('HOME_HTML_H1', 'Newsletter'),
        'author_label': g_loc.get('HTML_AUTHOR_LABEL', 'Author'),
        'source_label': g_loc.get('HTML_SOURCE_LABEL', 'Source'),
        't1': t1,
        't1_articles': g_home.get('News', []),  # Default to empty list if 'News' key doesn't exist
        't2': t2,
        't2_title': story_data['t2_title'],
        't2_content': story_data['t2_content'],
        't2_image': story_data['t2_image'],
        't2_image_alt': story_data['t2_image_alt'],
        't2_author': story_data['t2_author'],
        't2_source': story_data['t2_source'],
        't2_src_url': story_data['t2_src_url'],
        't3': t3,
        't3_articles': g_home.get('Events', []),  # Default to empty list if 'Events' key doesn't exist
        't4_greeting': g_loc.get('HOME_HTML_T4_GREETING', 'Thank you for subscribing!'),
        't4_team': g_loc.get('HOME_HTML_T4_TEAM', 'The Team'),
        'ft_url': ft_svr,
        'ops_svr': os.getenv("OPS_SVR", "http://localhost:5566"),
        'title': g_loc.get('HOME_HTML_H1', 'Newsletter')
    })
    
    try:
        log.info(f"Attempting to send newsletter to {len(emails)} recipients in language: {lang}")
        log.debug(f"Context keys: {list(context.keys())}")
        
        # Log important context data for debugging
        if 't1_articles' in context:
            log.debug(f"Found {len(context['t1_articles'])} news articles")
        if 't3_articles' in context:
            log.debug(f"Found {len(context['t3_articles'])} event articles")
            
        # Send the newsletter
        if eu.send_newsletter(g_fmail, emails, context):
            success_msg = f"Newsletter sent successfully to {len(emails)} recipients in language: {lang}"
            log.info(success_msg)
            flash(g_loc.get("PUB_HTML_SUCCESS", "Newsletter sent successfully."), 'success')
        else:
            error_msg = f"Failed to send newsletter for language: {lang}. Check logs for details."
            log.error(error_msg)
            flash(g_loc.get("PUB_HTML_FAIL", "Failed to send newsletter. Please try again later."), 'danger')
            
    except Exception as e:
        error_msg = f"Unexpected error while sending newsletter for language {lang}: {str(e)}"
        log.error(error_msg, exc_info=True)
        flash(g_loc.get("PUB_HTML_FAIL", "An unexpected error occurred. Please contact support."), 'danger')
        
    return redirect(url_for('home'))    

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset requests and form submission"""
    if request.method == 'GET':
        # Show the reset password form
        token = request.args.get('token')
        email = request.args.get('email')
        
        if not token or not email:
            flash('Invalid password reset link', 'error')
            return redirect(url_for('home'))
            
        # Verify the token
        if not dbm.verify_reset_token(email, token):
            flash('The password reset link is invalid or has expired.', 'error')
            return redirect(url_for('home'))
            
        return render_template('reset_password.html', 
                             email=email, 
                             token=token,
                             **get_template_context())
    
    elif request.method == 'POST':
        # Process the password reset form
        email = request.form.get('email')
        token = request.form.get('token')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([email, token, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(request.url)
            
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(request.url)
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return redirect(request.url)
        
        # Verify the token again before allowing password reset
        if not dbm.verify_reset_token(email, token):
            flash('The password reset link is invalid or has expired.', 'error')
            return redirect(url_for('home'))
        
        # Update the password
        if dbm.update_user_password(email, password):
            flash('Your password has been reset successfully. Please log in with your new password.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Failed to reset password. Please try again.', 'error')
            return redirect(request.url)

# Handle CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({
        'error': 'Invalid CSRF token',
        'message': 'The form has expired. Please refresh the page and try again.'
    }), 400

def main():
    """
    Main function
    
    Start Flask server
    """
    log.info("Starting FamilyTreesOps server...")
    # app.run(host='0.0.0.0', port=os.getenv("OPS_SVR_PORT", 5555), use_reloader=False)
    app.run(port=os.getenv("OPS_SVR_PORT", 5566), debug=True)

# Initialize global variables
init_globals()

if __name__ == "__main__":
    main()
