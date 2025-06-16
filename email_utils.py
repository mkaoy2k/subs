import os
import re
import secrets
import time
import smtplib
from flask_mail import Message
from flask import url_for, render_template
from dotenv import load_dotenv
import socket
import logging

# Configure logging
log = logging.getLogger(__name__)
# Set log level from environment variable or default to WARNING
log_level = os.getenv('LOGGING', 'WARNING').upper()
log.setLevel(getattr(logging, log_level, logging.WARNING))

# Email configuration
class Config:
    # Email server configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))  # Default to port 465 with SSL
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() in ['true', '1', 't']
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@familytree.com')
    MAIL_TIMEOUT = 30  # 30 seconds timeout
    MAIL_DEBUG = True  # Enable debug output
    MAIL_ASCII_ATTACHMENTS = False  # Handle non-ASCII attachments properly
    MAIL_SUPPRESS_SEND = False  # Actually send emails
    
    # Application configuration
    APP_NAME = os.getenv('APP_NAME', 'FamilyTrees')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8501')

def validate_email(email):
    """
    Check if email is legitimate.
    Return True if passed else False.
    """
    pattern = r"^[a-zA-Z0-9-_.]+@[a-zA-Z0-9-]+\.[a-z]{2,4}$"

    if re.match(pattern, email):
        return True
    return False

def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)

def send_verification_email(mail, email, token, is_subscribe=True):
    """
    Send a verification email for subscription or unsubscription with retry logic
    
    Args:
        mail: Flask-Mail instance
        email (str): Recipient's email address
        token (str): Verification token
        is_subscribe (bool): True for subscription, False for unsubscription
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    log.debug(f"Preparing to send verification email to {email}")
    action = 'subscribe' if is_subscribe else 'unsubscribe'
    subject = f"Please confirm that you want to {action} to {Config.APP_NAME}"
    
    try:
        # Create verification URL
        verification_url = url_for(
            'verify_email',
            email=email,
            token=token,
            action=action,
            _external=True,
            _scheme='https' if 'https' in Config.BASE_URL else 'http'
        )
        log.debug(f"Generated verification URL: {verification_url}")
    except Exception as e:
        log.error(f"Failed to generate verification URL: {str(e)}")
        return False
    
    try:
        # Render email template
        html = render_template(
            'email/verification.html',
            action=action,
            verification_url=verification_url,
            app_name=Config.APP_NAME,
            email=email
        )
        log.debug("Successfully rendered email template")
        
        # Configure email message
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html,
            sender=Config.MAIL_DEFAULT_SENDER
        )
        log.debug(f"Prepared email message - From: {Config.MAIL_DEFAULT_SENDER}, To: {email}")
        
        # Log SMTP configuration (without sensitive data)
        log.debug(f"SMTP Server: {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
        log.debug(f"Using TLS: {Config.MAIL_USE_TLS}, Using SSL: {Config.MAIL_USE_SSL}")
        
        # Send the email using the helper function
        result = _send_mail(mail, msg)
            
        if result:
            log.debug(f"Verification email sent successfully to {email} for {'subscription' if is_subscribe else 'unsubscription'}")
        else:
            log.warning(f"Failed to send verification email to {email} for {'subscription' if is_subscribe else 'unsubscription'}")
                
        return result
            
    except Exception as e:
        log.error(f"Failed to prepare email: {str(e)}", exc_info=True)
        return False

def send_newsletter(mail, emails, blob):
    """
    Send newsletter to the specified email addresses
    
    Args:
        mail: Flask-Mail instance
        email (list): Recipient's email addresses
        blob (dict): Blob of data containing email content
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    log.info(f"Preparing to send newsletter to {emails}")
    log.debug(f"Email blob keys: {list(blob.keys())}")

    try:
        # Log article counts for debugging
        if 't1_articles' in blob:
            log.debug(f"Found {len(blob['t1_articles'])} articles in t1_articles")
        if 't3_articles' in blob:
            log.debug(f"Found {len(blob['t3_articles'])} articles in t3_articles")

        # Render newsletter template
        log.debug("Rendering newsletter template...")
        try:
            html = render_template(
                'email/newsletter.html',
                header=blob.get('header', ''),
                t1=blob.get('t1', ''),
                t1_articles=blob.get('t1_articles', []),
                t2=blob.get('t2', ''),
                t2_title=blob.get('t2_title', ''),
                t2_content=blob.get('t2_content', ''),
                t2_image=blob.get('t2_image', ''),
                t2_image_alt=blob.get('t2_image_alt', ''),
                t3=blob.get('t3', ''),
                t3_articles=blob.get('t3_articles', []),
                ft_url=blob.get('ft_url', ''),
                motto_btn=blob.get('motto_btn', ''),
                motto=blob.get('motto', ''),
                t4_greeting=blob.get('t4_greeting', ''),
                t4_team=blob.get('t4_team', ''),
                title=blob.get('title', 'Newsletter')
            )
            log.debug(f"Successfully rendered newsletter template. HTML length: {len(html)} characters")
            log.debug(f"First 200 chars: {html[:200]}...")
        except Exception as template_error:
            log.error(f"Error rendering template: {str(template_error)}", exc_info=True)
            raise
        
        # Configure newsletter message
        try:
            subject = blob.get('title', 'The Kaos Newsletter')
            log.debug(f"Creating email with subject: {subject}")
            
            msg = Message(
                subject=subject,
                recipients=emails,
                html=html,
                sender=Config.MAIL_DEFAULT_SENDER
            )
            
            log.debug(f"Prepared newsletter - From: {Config.MAIL_DEFAULT_SENDER}")
            log.debug(f"Recipients: {', '.join(emails) if isinstance(emails, list) else emails}")
            log.debug(f"Subject: {msg.subject}")
            log.debug(f"Body length: {len(html)} characters")
            
            # Log SMTP configuration (without sensitive data)
            log.debug(f"SMTP Server: {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
            log.debug(f"Using TLS: {Config.MAIL_USE_TLS}, Using SSL: {Config.MAIL_USE_SSL}")
            log.debug(f"Mail server timeout: {Config.MAIL_TIMEOUT} seconds")
            log.debug(f"Mail debug mode: {Config.MAIL_DEBUG}")
            
            # Log first 200 characters of HTML for verification
            log.debug(f"HTML Preview: {html[:200]}...")
            
            log.info(f"Sending newsletter to {len(emails) if isinstance(emails, list) else 1} recipient(s)")
            
            # Send the email using the helper function
            result = _send_mail(mail, msg)
            
            if result:
                log.debug("Newsletter sent successfully")
            else:
                log.warning("Failed to send newsletter after retries")
                
            return result
            
        except Exception as msg_error:
            log.error(f"Error creating or sending message: {str(msg_error)}", exc_info=True)
            raise
                
    except Exception as e:
        log.error(f"Failed to prepare email: {str(e)}", exc_info=True)
        return False
    
def _send_mail(mail, msg, max_retries=3):
    """
    Helper function to send email with retry logic
    
    Args:
        mail: Flask-Mail instance
        msg: Email message to send
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    for attempt in range(max_retries):
        try:
            log.info(f"Attempt {attempt + 1}/{max_retries} to send email to {msg.recipients}")
            
            # Test SMTP connection first
            try:
                with mail.connect() as conn:
                    log.debug("Successfully connected to SMTP server")
                    log.info(f"Sending email to {msg.recipients}...")
                    conn.send(msg)
                    log.info(f"Successfully sent email to {msg.recipients}")
                    return True
                    
            except smtplib.SMTPAuthenticationError as e:
                log.error(f"SMTP Authentication Error: {str(e)}")
                log.error("Please check your email credentials and ensure you're using an App Password if using Gmail")
                return False
                
            except smtplib.SMTPException as e:
                log.error(f"SMTP Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    log.error(f"Failed to send email after {max_retries} attempts")
                    return False
                    
            except (socket.timeout, socket.gaierror) as e:
                log.error(f"Network Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    log.error("Network connection failed. Please check your internet connection and firewall settings.")
                    return False
                    
            except Exception as e:
                log.error(f"Unexpected error (attempt {attempt + 1}/{max_retries}): {str(e)}", exc_info=True)
                if attempt == max_retries - 1:
                    return False
            
            # Wait before retrying (exponential backoff)
            wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
            log.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            
        except Exception as e:
            log.error(f"Error during email sending attempt {attempt + 1}: {str(e)}", exc_info=True)
            if attempt == max_retries - 1:
                return False
    
    return False
