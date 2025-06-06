#!/usr/bin/env python3
"""
Test SMTP connection to Gmail's SMTP server.
"""

import smtplib
import socket
import ssl
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection to Gmail's server using SSL."""
    smtp_server = 'smtp.gmail.com'  # Gmail's SMTP server
    port = 465  # SSL port
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    if not username or not password:
        print("❌ Error: MAIL_USERNAME and MAIL_PASSWORD must be set in .env file")
        return False
    
    print(f"🔍 Testing SMTP SSL connection to {smtp_server}:{port}...")
    print(f"📧 Using account: {username}")
    
    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        
        print("\n1. Creating SMTP_SSL connection...")
        server = smtplib.SMTP_SSL(smtp_server, port, context=context, timeout=30)
        print(f"   ✅ Connected to {smtp_server}:{port} via SSL")
        
        # Enable debug output
        server.set_debuglevel(1)
        
        print("\n2. Sending EHLO...")
        server.ehlo()
        print("   ✅ EHLO successful")
        
        print("\n3. Attempting to log in...")
        server.login(username, password)
        print("   ✅ Successfully logged in!")
        
        print("\n4. Quitting server...")
        server.quit()
        print("   ✅ Successfully disconnected")
        
        print("\n✅ SMTP SSL test completed successfully!")
        return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please check your username and password.")
        print("   If using Gmail, make sure to use an App Password instead of your regular password.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred: {e}")
    except socket.timeout:
        print("❌ Connection timed out. Check your network connection and firewall settings.")
    except socket.gaierror:
        print(f"❌ Could not resolve hostname: {smtp_server}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    
    return False

if __name__ == "__main__":
    test_smtp_connection()
