import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("MAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


def send_email(receiver, otp=None, subject="BloodNeed OTP", body=None):
    if not EMAIL or not EMAIL_PASSWORD:
        raise Exception("MAIL_USERNAME or MAIL_PASSWORD missing in .env")

    if body is None:
        if otp is None:
            body = "Hello,\n\nThis is a BloodNeed message.\n\nRegards,\nBloodNeed Team\n"
        else:
            body = f"""Hello,

Your BloodNeed OTP is: {otp}

This OTP is valid for 15 minutes.

Regards,
BloodNeed Team
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    try:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, receiver, msg.as_string())
    finally:
        try:
            server.quit()
        except Exception:
            pass