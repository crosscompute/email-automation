# https://realpython.com/python-send-email
'''
python send.py \
    tests/standard/input/contacts.csv \
    tests/standard/input \
    tests/standard/input \
    smtp.gmail.com \
    465 \
    you@gmail.com \
    you@gmail.com
'''
import pandas as pd
import re
import ssl
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from markdown import markdown
from os.path import basename, join
from smtplib import SMTP_SSL
from sys import argv


HTML_ENDING_TAG_PATTERN = re.compile(r'</[a-z]>')


def might_be_html(text):
    if HTML_ENDING_TAG_PATTERN.search(text):
        return True
    return False


def get_message_packet(row, templates_folder, attachments_folder):


def run(
        contacts_path,
        templates_folder,
        attachments_folder,
        smtp_url,
        smtp_port,
        smtp_username,
        smtp_password):
    context = ssl.create_default_context()
    with SMTP_SSL(smtp_url, smtp_port, context=context) as smtp_server:
        smtp_server.login(smtp_username, smtp_password)

        for row_index, row in contacts_table.iterrows():
            message_packet = get_message_packet(
                row, templates_folder, attachments_folder)
            target_email = message_packet['target_email']
            target_payload = message_packet['target_payload']
            smtp_server.sendmail(source_email, target_email, target_payload)
