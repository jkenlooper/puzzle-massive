import smtplib
from email.mime.text import MIMEText

from flask import current_app


def send_message(to, subject, body, config):
    """
    Send a message via smtp.
    """
    # Create a text/plain message
    msg = MIMEText(body)

    host = config.get("SMTP_HOST")
    port = config.get("SMTP_PORT")
    user = config.get("SMTP_USER")
    password = config.get("SMTP_PASSWORD")
    sender = config.get("EMAIL_SENDER")

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    # Return early if any of the above are None
    if not (host and port and user and password and sender):
        current_app.logger.warning(
            f"""
Site not configured for email. The below message has NOT been sent:

${msg}

"""
        )
        return

    current_app.logger.info(
        f"""
Sending

${msg}

"""
    )
    server = smtplib.SMTP()
    server.connect(host, port)
    server.starttls()
    server.login(user, password)

    server.sendmail(sender, [to], msg.as_string())
    server.quit()
