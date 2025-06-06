
import os
from dotenv import load_dotenv  # pip install python-dotenv
import json

# Import email packages
import email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

# Using 'smtplib' module to create an SMTP client session object 
# that sends an email to any SMTP server
import smtplib

# Tempory file module
import tempfile

def load_menu(fn):

    # reading the data from the language-definition file
    with open(fn) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    return js

# --- Load supported L10N dictionaries ---
def load_L10N(f_l10n):
    # Build and return a dictionary for all supported languages, 
    # with key of language name and associated L10N dictionaries.
    # Load the environment variables from file
    
    # reading the data from the language-definition file
    with open(f_l10n) as f:
        data = f.read()
        
    # reconstructing languages as a dictionary
    js = json.loads(data)
    
    dl10n = {}
    # iterate all supported languages
    for key, fl in js.items():
        # load each language-specific L10N settings
        with open(fl) as f:
            data = f.read()
      
        # reconstructing the data as a dictionary
        d = json.loads(data)
        dl10n[key] = d
  
    return dl10n

# Functional testing
if __name__ == '__main__':
    path_dir = 'data'  # relative to the current dir
    email_receiver = "mkaoy2k@yahoo.com"
    confirm_template = f"{path_dir}/confirm.html"
    email_text = f'{path_dir}/template.txt'
    email_html = f'{path_dir}/template.html'
    email_attached = f'{path_dir}/template.png'

    try:
        verify_email(email_receiver, # receiver
            "Henry Kao",      # full name
            "hkao",             # username
            "abc123",           # msg
            confirm_template,   # template
            )
        print(f"confirmation successfully sent, check {email_receiver}")   
                            
    except Exception as err:
        print(f"Caught '{err}'. class is {type(err)}")
        print(f"send confirm email failed")    
        
    # try:
    #     send_email(email_receiver,
    #         subject="Test1",
    #         )
    #     print(f'No body email sent to {email_receiver} ok\n')
        
    #     send_email(email_receiver,
    #         subject="Test2",
    #         f_text=email_text,
    #         )
    #     print(f'Text email sent to {email_receiver} ok\n')

    #     send_email(email_receiver,
    #         subject="Test3",
    #         f_text=email_text,
    #         f_html=email_html,
    #         )
    #     print(f'Text & HTML email sent to {email_receiver} ok\n')

    #     send_email(email_receiver,
    #         subject="Test4",
    #         f_text=email_text,
    #         f_html=email_html,
    #         f_attached=email_attached 
    #         )
    #     print(f'Text & HTML Email with attachment sent to {email_receiver} ok\n')

    # except Exception as err:
    #     print(f"Caught '{err}'. class is {type(err)}")
    #     print(f'send_email(): failed\n')
