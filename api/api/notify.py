import smtplib
from email.mime.text import MIMEText

from flask import current_app

def send_message(to, subject, body):
    """
    Send a message via smtp.
    """
    # Create a text/plain message
    msg = MIMEText(body)

    host = current_app.config.get('SMTP_HOST')
    port = current_app.config.get('SMTP_PORT')
    user = current_app.config.get('SMTP_USER')
    password = current_app.config.get('SMTP_PASSWORD')
    sender = current_app.config.get('EMAIL_SENDER')
    # TODO: fail early if any of the above are None

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    server = smtplib.SMTP()
    server.connect(host, port)
    server.starttls()
    server.login(user, password)

    server.sendmail(sender, [to], msg.as_string())
    server.quit()
