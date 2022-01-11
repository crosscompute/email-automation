# TODO: Accept uploaded attachments
import json
import ssl
from datetime import datetime
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from invisibleroads_macros_disk import is_path_in_folder
from invisibleroads_macros_log import format_path
from markdown import markdown
from os import environ
from os.path import basename, exists, join
from pandas import read_csv
from smtplib import SMTPException, SMTP_SSL as SMTPServer
from sys import argv


def run(
        smtp_url, smtp_port, smtp_username, smtp_password, source_email,
        subject_template_text, body_template_text, contacts_table,
        attachments_folder, log):
    try:
        contact_dictionaries = get_contact_dictionaries(
            contacts_table, attachments_folder)
    except OSError:
        raise
    message_count = len(contact_dictionaries)
    context = ssl.create_default_context()
    try:
        with SMTPServer(smtp_url, smtp_port, context=context) as smtp_server:
            smtp_server.login(smtp_username, smtp_password)
            for message_index, contact_dictionary in enumerate(
                    contact_dictionaries):
                message_packet = get_message_packet(
                    contact_dictionary, subject_template_text,
                    body_template_text, attachments_folder)
                target_email = message_packet['target_email']
                target_payload = message_packet['target_payload']
                smtp_server.sendmail(
                    source_email, target_email, target_payload)
                log(f'{message_index + 1} of {message_count} sent')
    except SMTPException:
        raise


def get_contact_dictionaries(contacts_table, attachments_folder):
    contact_dictionaries = []
    for row_index, row in contacts_table.iterrows():
        attachment_paths = []
        for k, v in row.items():
            if not k.endswith('_path'):
                continue
            path = join(attachments_folder, v.strip())
            if not exists(path):
                raise OSError(f'{format_path(path)} does not exist')
            elif not is_path_in_folder(path, attachments_folder):
                raise OSError(
                    f'{format_path(path)} path is outside '
                    f'{format_path(attachments_folder)}')
            attachment_paths.append(path)
        contact_dictionaries.append(dict(row) | {
            'target_email': row['email'],
            'attachment_paths': attachment_paths,
        })
    return contact_dictionaries


def get_message_packet(
        d, subject_template_text, body_template_text, attachments_folder):
    attachment_paths = d['attachment_paths']
    target_email = d['target_email']
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
        path = join(attachments_folder, attachment_path)
        with open(path, 'rb') as f:
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
    variables = json.load(open(join(
        input_folder, 'variables.dictionary'), 'rt'))
    source_email = variables['source_email']
    subject_template_text = variables['subject']
    body_template_text = variables['body']
    contacts_table = read_csv(join(input_folder, 'contacts.csv'))

    def log(text):
        open(join(output_folder, 'log.txt'), 'at').write(
            datetime.now().strftime('%Y%m%d-%H%M') + ': ' + text + '\n')

    try:
        run(
            smtp_url, smtp_port, smtp_username, smtp_password, source_email,
            subject_template_text, body_template_text, contacts_table,
            attachments_folder, log)
    except (OSError, SMTPException) as e:
        log(str(e))
        raise SystemExit
