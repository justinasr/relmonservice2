"""
Module that handles all email notifications
"""
import smtplib
import logging
import json
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText


class EmailSender():

    def __init__(self, config):
        self.logger = logging.getLogger('logger')
        self.credentials = config['ssh_credentials']
        self.smtp = None

    def __setup_smtp(self):
        if ':' not in self.credentials:
            with open(self.credentials) as json_file:
                credentials = json.load(json_file)
        else:
            credentials = {}
            credentials['username'] = self.credentials.split(':')[0]
            credentials['password'] = self.credentials.split(':')[1]

        self.logger.info('Credentials loaded successfully: %s', credentials['username'])
        self.smtp = smtplib.SMTP(host='smtp.cern.ch', port=587)
        # self.smtp.connect()
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.ehlo()
        self.smtp.login(credentials['username'], credentials['password'])

    def __close_smtp(self):
        self.smtp.quit()
        self.smtp = None

    def send(self, subject, body, recipients, files=None):
        body = body.strip()
        body += '\n\nSincerely,\nRelMon Service'
        # Create a fancy email message
        message = MIMEMultipart()
        message['Subject'] = '[RelMon] %s' % (subject)
        message['From'] = 'PdmV Service Account <pdmvserv@cern.ch>'
        message['To'] = ', '.join(recipients)
        message['Cc'] = 'PdmV Service Account <pdmvserv@cern.ch>'
        # Set body text
        message.attach(MIMEText(body))
        if files:
            for path in files:
                attachment = MIMEBase('application', 'octet-stream')
                with open(path, 'rb') as f:
                    attachment.set_payload(f.read())

                file_name = path.split('/')[-1]
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition',
                                      'attachment; filename="%s"' % (file_name))
                message.attach(attachment)

        self.logger.info('Will send "%s" to %s', message['Subject'], message['To'])
        self.__setup_smtp()
        self.smtp.sendmail(message['From'], message['To'], message.as_string())
        self.__close_smtp()