import os
import secrets
from flask_mail import Message
from flask import url_for, render_template
from dotenv import load_dotenv

# Load environment variables from specific config file
load_dotenv('.env')

# Email configuration
class Config:
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@familytree.com')
    APP_NAME = os.getenv('APP_NAME', 'FamilyTrees Ops Server')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8501')

def validate_email(email):
    """
    Check if email is legitimate.
    Return True if passed else False.
    """
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$" 

    if re.match(pattern, email):
        return True
    return False

def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

def send_verification_email(mail, email, token, is_subscribe=True):
    """
    Send a verification email for subscription or unsubscription
    
    Args:
        mail: Flask-Mail instance
        email (str): Recipient's email address
        token (str): Verification token
        is_subscribe (bool): True for subscription, False for unsubscription
    """
    action = 'subscribe' if is_subscribe else 'unsubscribe'
    subject = f"Please confirm your {action} to {Config.APP_NAME}"
    
    # Create verification URL
    verification_url = url_for(
        'verify_email',
        email=email,
        token=token,
        action=action,
        _external=True,
        _scheme='https' if 'https' in Config.BASE_URL else 'http'
    )
    
    # Render email template
    html = render_template(
        'email/verification.html',
        action=action,
        verification_url=verification_url,
        app_name=Config.APP_NAME,
        email=email
    )
    
    # Create and send message
    msg = Message(
        subject=subject,
        recipients=[email],
        html=html,
        sender=Config.MAIL_DEFAULT_SENDER
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
