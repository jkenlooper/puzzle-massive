import smtplib
from email.mime.text import MIMEText

def send_message(to, subject, body, config):
    """
    Send a message via smtp.
    """
    # Create a text/plain message
    msg = MIMEText(body)

    host = config.get('SMTP_HOST')
    port = config.get('SMTP_PORT')
    user = config.get('SMTP_USER')
    password = config.get('SMTP_PASSWORD')
    sender = config.get('EMAIL_SENDER')
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
