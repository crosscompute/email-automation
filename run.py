# TODO: Accept uploaded attachments
import json
import ssl
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from markdown import markdown
from os import environ
from os.path import basename, join
from pandas import read_csv
from smtplib import SMTPException, SMTP_SSL as SMTPServer
from sys import argv


def run(
        smtp_url, smtp_port, smtp_username, smtp_password, source_email,
        subject_template_text, body_template_text, contacts_table,
        attachments_folder, log):
    messages_total_count = len(contacts_table)
    context = ssl.create_default_context()
    try:
        with SMTPServer(smtp_url, smtp_port, context=context) as smtp_server:
            smtp_server.login(smtp_username, smtp_password)
            for row_index, row in contacts_table.iterrows():
                log(row_index, messages_total_count)
                message_packet = get_message_packet(
                    row, subject_template_text, body_template_text,
                    attachments_folder)
                target_email = message_packet['target_email']
                target_payload = message_packet['target_payload']
                smtp_server.sendmail(
                    source_email, target_email, target_payload)
        log(row_index + 1, messages_total_count)
    except SMTPException as e:
        print(e)


def get_message_packet(
        d, subject_template_text, body_template_text, attachments_folder):
    attachment_paths = [v for k, v in d.items() if k.endswith('_path')]
    target_email = d['email']
    subject_text = render_template(subject_template_text, d)
    body_text = render_template(body_template_text, d)
    body_html = render_template(body_template_text, d, from_markdown=True)

    message = MIMEMultipart('alternative')
    message['From'] = source_email
    message['To'] = target_email
    message['Subject'] = subject_text
    message['Bcc'] = target_email
    message.attach(MIMEText(body_text, 'plain'))
    message.attach(MIMEText(body_html, 'html'))

    for attachment_path in attachment_paths:
        attachment_name = basename(attachment_path)
        attachment_part = MIMEBase('application', 'octet-stream')
        with open(join(attachments_folder, attachment_path), 'rb') as f:
            attachment_part.set_payload(f.read())
        encode_base64(attachment_part)
        attachment_part.add_header(
            'Content-Disposition', f'attachment; filename={attachment_name}')
        message.attach(attachment_part)
    return {
        'target_email': target_email,
        'target_payload': message.as_string(),
    }


def render_template(template_text, value_by_key, from_markdown=False):
    template_text = template_text.format(**value_by_key)
    if from_markdown:
        template_text = markdown(template_text)
    return template_text.strip()


if __name__ == '__main__':
    input_folder, output_folder = argv[1:]
    attachments_folder = environ['ATTACHMENTS_FOLDER']
    smtp_url = environ['SMTP_URL']
    smtp_port = environ['SMTP_PORT']
    smtp_username = environ['SMTP_USERNAME']
    smtp_password = environ['SMTP_PASSWORD']
    variables = json.load(open(join(input_folder, 'variables.json'), 'rt'))
    source_email = variables['source_email']
    subject_template_text = variables['subject']
    body_template_text = variables['body']
    contacts_table = read_csv(join(input_folder, 'contacts.csv'))

    def log(index, count):
        print(index, count)
        json.dump({
            'messages_sent_count': index,
            'messages_total_count': count,
        }, open(join(output_folder, 'variables.json'), 'wt'))

    run(
        smtp_url, smtp_port, smtp_username, smtp_password, source_email,
        subject_template_text, body_template_text, contacts_table,
        attachments_folder, log)
