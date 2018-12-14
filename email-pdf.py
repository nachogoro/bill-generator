#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fromaddr',
                        help='Sender of the e-mail',
                        type=str,
                        default='your-from-addr@gmail.com',
                        action='store')
    parser.add_argument('--toaddr',
                        help='Receiver of the e-mail',
                        type=str,
                        default='your-receiver-addr@gmail.com',
                        action='store')

    parser.add_argument('--attachment', help='File to be attached',
                        type=str, action='store')

    parser.add_argument('body', help='File containing the body of the message',
                        type=str)

    args = parser.parse_args()

    with open(args.body, 'rb') as src:
        body = src.read()

    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address
    msg['From'] = args.fromaddr

    # storing the receivers email address
    msg['To'] = args.toaddr

    # storing the subject
    msg['Subject'] = 'Invoice for current month'

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain', 'UTF-8'))

    if args.attachment:
        # open the file to be sent
        attachment = open(args.attachment, 'rb')

        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')

        # To change the payload into encoded form
        p.set_payload((attachment).read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header('Content-Disposition',
                     'attachment; filename= %s' % os.path.basename(args.attachment))

        # attach the instance 'p' to instance 'msg'
        msg.attach(p)

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(args.fromaddr, 'INSERT-PASSWORD-HERE')

    # sending the mail
    s.sendmail(args.fromaddr, args.toaddr, text)

    # terminating the session
    s.quit()


if __name__ == '__main__':
    main()
