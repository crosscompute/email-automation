# TODO: Accept uploaded attachments
import json
from os import environ
from os.path import join
from pandas import read_csv
from sys import argv


ATTACHMENTS_FOLDER = environ['ATTACHMENTS_FOLDER']
SMTP_URL = environ['SMTP_URL']
SMTP_PORT = environ['SMTP_PORT']
SMTP_USERNAME = environ['SMTP_USERNAME']
SMTP_PASSWORD = environ['SMTP_PASSWORD']


def render_template(template_text, value_by_key, from_markdown=False):
    template_text = template_text.format(**value_by_key)
    if from_markdown:
        template_text = markdown(template_text)
    return template_text.strip()


input_folder, output_folder = argv[1:]
variables = json.load(open(join(input_folder, 'variables.json'), 'rt'))
subject_template_text = variables['subject']
body_template_text = variables['body']
source_email = variables['email']
contacts_table = read_csv(join(input_folder, 'contacts.csv'))


def get_message_packet(row, attachments_folder):
    attachment_paths = [
        value for key, value in row.items()
        if key.startswith('attachment') and key.endswith('_path')]
    target_email = row['email']
    subject_text = render_template(subject_template_text, row)
    body_text = render_template(body_template_text, row)
    body_html = render_template(body_template_text, row, from_markdown=True)

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
        with open(join(
            attachments_folder, attachment_path,
        ), 'rb') as attachment_file:
            attachment_part.set_payload(attachment_file.read())
        encode_base64(attachment_part)
        attachment_part.add_header(
            'Content-Disposition', f'attachment; filename={attachment_name}')
        message.attach(attachment_part)

    return {
        'target_email': target_email,
        'target_payload': message.as_string(),
    }
