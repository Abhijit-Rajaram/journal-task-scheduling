from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from main.config import settings

def send_email(subject, html_body, to_email):
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.starttls()
    server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
