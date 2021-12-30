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
from getpass import getpass
from markdown import markdown
from os.path import basename, join
from smtplib import SMTP_SSL
from sys import argv


HTML_ENDING_TAG_PATTERN = re.compile(r'</[a-z]>')


def might_be_html(text):
    if HTML_ENDING_TAG_PATTERN.search(text):
        return True
    return False


def render_template(template_path, value_by_key, from_markdown=False):
    template_file = open(template_path, 'rt')
    template_text = template_file.read()
    template_text = template_text.format(**value_by_key)
    if from_markdown:
        template_text = markdown(template_text)
    return template_text.strip()


def get_message_packet(row, templates_folder, attachments_folder):
    attachment_paths = [
        value for key, value in row.items()
        if key.startswith('attachment') and key.endswith('_path')]

    target_email = row['email']

    subject_path = row['subject_path']
    subject_text = render_template(join(
        templates_folder, subject_path), row)

    text_path = row['text_path']
    body_text = render_template(join(
        templates_folder, text_path), row)

    markdown_path = row['markdown_path']
    body_html = render_template(join(
        templates_folder, markdown_path), row, from_markdown=True)

    if body_text and body_html:
        is_multipart = True
        message = MIMEMultipart('alternative')
    elif attachment_paths:
        is_multipart = True
        message = MIMEMultipart()
    else:
        is_multipart = False

    if is_multipart:
        message['From'] = source_email
        message['To'] = target_email
        message['Subject'] = subject_text
        message['Bcc'] = target_email
        if body_text:
            message.attach(MIMEText(body_text, 'plain'))
        if body_html:
            message.attach(MIMEText(body_html, 'html'))

    for attachment_path in attachment_paths:
        attachment_name = basename(attachment_path)
        attachment_part = MIMEBase('application', 'octet-stream')
        with open(join(
            attachments_folder, attachment_path,
        ), 'rb') as attachment_file:
            attachment_part.set_payload(attachment_file.read())
        encode_base64(attachment_part)
        attachment_part.add_header(
            'Content-Disposition', f'attachment; filename={attachment_name}')
        message.attach(attachment_part)

    payload = message.as_string() if is_multipart else body_text

    return {
        'target_email': target_email,
        'target_payload': payload,
    }


def run(
        contacts_path,
        templates_folder,
        attachments_folder,
        smtp_url,
        smtp_port,
        smtp_username,
        smtp_password):
    contacts_table = pd.read_csv(contacts_path)

    context = ssl.create_default_context()
    with SMTP_SSL(smtp_url, smtp_port, context=context) as smtp_server:
        smtp_server.login(smtp_username, smtp_password)

        for row_index, row in contacts_table.iterrows():
            message_packet = get_message_packet(
                row, templates_folder, attachments_folder)
            target_email = message_packet['target_email']
            target_payload = message_packet['target_payload']
            smtp_server.sendmail(source_email, target_email, target_payload)


if __name__ == '__main__':
    [
        contacts_path,
        templates_folder,
        attachments_folder,
        smtp_url,  # smtp.gmail.com
        smtp_port,  # 465
        smtp_username,  # sender_email
        source_email,
    ] = argv[1:]
    smtp_password = getpass()
    run(
        contacts_path,
        templates_folder,
        attachments_folder,
        smtp_url,
        smtp_port,
        smtp_username,
        smtp_password)
