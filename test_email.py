#!/usr/bin/env python3
"""
Test script for email functionality.
Run this directly to test sending a verification email.
"""

import os
import logging
from email_utils import generate_verification_token, send_verification_email
from flask import Flask
from flask_mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def main():
    """Test sending a verification email."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log = logging.getLogger(__name__)
    
    # Configure test Flask app
    test_app = Flask(__name__)
    
    # Required for URL generation outside of request context
    test_app.config.update(
        SERVER_NAME='localhost:8501',
        PREFERRED_URL_SCHEME='https',
        APPLICATION_ROOT='/',
        
        # Gmail SMTP Configuration with SSL
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=465,  # Port 465 with SSL
        MAIL_USE_TLS=False,  # Disable TLS when using SSL
        MAIL_USE_SSL=True,  # Enable SSL
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),  # Your Gmail address
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),  # Your App Password
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER'),
        MAIL_DEBUG=True,  # Enable debug output
        MAIL_SUPPRESS_SEND=False,  # Actually send emails
        MAIL_TIMEOUT=30,  # 30 seconds timeout
        MAIL_ASCII_ATTACHMENTS=False,  # Handle non-ASCII attachments properly
        MAIL_MAX_EMAILS=None,  # No limit on number of emails
        MAIL_DEFAULT_SENDER_NAME=None,  # No custom sender name
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-for-testing'),
        
        # App configuration
        APP_NAME=os.getenv('APP_NAME', 'FamilyTrees Ops Server'),
        BASE_URL=os.getenv('BASE_URL', 'http://localhost:8501')
    )
    
    # Initialize Flask-Mail
    test_mail = Mail(test_app)
    
    # Test email details
    test_email = os.getenv('TEST_EMAIL', 'test@example.com')
    test_token = generate_verification_token()
    
    print(f"Sending test email to {test_email}...")
    
    # Register the verification endpoint that matches what email_utils expects
    @test_app.route('/verify_email')
    def verify_email():
        return "Email verification endpoint"
    
    try:
        # Set up the application context and test the email sending
        with test_app.app_context():
            # Set up test request context for URL generation
            with test_app.test_request_context(base_url='http://localhost:8501'):
                result = send_verification_email(
                    test_mail,
                    email=test_email,
                    token=test_token,
                    is_subscribe=True
                )
                
                if result:
                    print("✓ Test email sent successfully!")
                else:
                    print("✗ Failed to send test email after all retries")
    except Exception as e:
        print(f"✗ Error sending test email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
