import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

APPS_SCRIPT_URL = os.getenv(
    "OTP_EMAIL_SCRIPT_URL",
    "https://script.google.com/macros/s/AKfycbxmP2HdZQHgruSHihnp-3iKG8gE5Rut4ZDyEcgma-gcxuKH1Qh1KvGCEJ63HkKYdFOi/exec"
)

SECRET_TOKEN = os.getenv(
    "OTP_EMAIL_SECRET",
    "BloodNeed_OTP_2026"
)


def send_email(receiver, otp=None, subject="BloodNeed OTP", body=None):

    if not receiver:
        raise Exception("Receiver email is required")

    if not otp:
        raise Exception("OTP is required")

    payload = {
        "token": SECRET_TOKEN,
        "email": receiver,
        "otp": str(otp)
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        APPS_SCRIPT_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        print("GOOGLE APPS SCRIPT RESPONSE:", result)

        if not result.get("success"):
            raise Exception(
                result.get("message", "Email sending failed")
            )

        print("OTP EMAIL SENT SUCCESSFULLY:", receiver)
        return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print("EMAIL HTTP ERROR:", e.code, error_body)
        raise Exception(f"Email service HTTP error: {e.code}")

    except Exception as e:
        print("EMAIL SERVICE ERROR:", e)
        raise