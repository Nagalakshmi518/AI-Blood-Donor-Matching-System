import os
import json
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()


APPS_SCRIPT_URL = os.getenv(
    "OTP_EMAIL_SCRIPT_URL",
    "<YOUR_APPS_SCRIPT_EXEC_URL>"
)

SECRET_TOKEN = os.getenv(
    "OTP_EMAIL_SECRET",
    "BloodNeed_OTP_2026"
)


def send_email(
    receiver,
    otp=None,
    subject="BloodNeed",
    body=None
):
    """
    Sends BloodNeed emails through Google Apps Script.

    Supports:
    1. OTP verification emails
    2. Blood request notification emails
    3. Other normal project emails
    """

    if not receiver:
        raise Exception("Receiver email is required")

    # --------------------------------------
    # Create email body
    # --------------------------------------

    if body is None:

        if otp is not None:

            body = f"""Hello,

Your BloodNeed OTP is: {otp}

This OTP is valid for 15 minutes.

If you did not request this OTP, please ignore this email.

Regards,
BloodNeed Team
"""

        else:

            body = """Hello,

This is a message from BloodNeed.

Regards,
BloodNeed Team
"""

    # --------------------------------------
    # Prepare request for Google Apps Script
    # --------------------------------------

    payload = {
        "token": SECRET_TOKEN,
        "email": receiver,
        "subject": subject,
        "otp": str(otp) if otp is not None else "",
        "body": body
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

    # --------------------------------------
    # Send email
    # --------------------------------------

    try:

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            response_data = response.read().decode(
                "utf-8"
            )

        result = json.loads(response_data)

        print(
            "GOOGLE APPS SCRIPT RESPONSE:",
            result
        )

        if not result.get("success"):

            raise Exception(
                result.get(
                    "message",
                    "Email sending failed"
                )
            )

        print(
            "EMAIL SENT SUCCESSFULLY:",
            receiver
        )

        return True

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        print(
            "EMAIL HTTP ERROR:",
            e.code,
            error_body
        )

        raise Exception(
            f"Email service HTTP error: {e.code}"
        )

    except Exception as e:

        print(
            "EMAIL SERVICE ERROR:",
            e
        )

        raise