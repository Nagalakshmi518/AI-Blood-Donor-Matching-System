import random
from datetime import datetime, timedelta

from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash as werkzeug_hash

from app import db
from app.auth.utils import hash_password, verify_password, generate_token
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.user import User
from app.models.hospital import Hospital
from app.models.password_reset import PasswordReset
from app.models.email_verification import EmailVerification


def generate_verification_code():
    # 6-digit numeric code as string
    return str(random.randint(100000, 999999)).zfill(6)


def send_verification_code(email, otp, subject=None):
    try:
        from app.utils.email_service import send_email

        send_email(
            receiver=email,
            otp=otp,
            subject=subject or "BloodNeed OTP"
        )

        return True

    except Exception as e:
        print("Email sending error:", e)
        return False


def register_user(data):
    required_fields = [
        "full_name",
        "email",
        "phone",
        "password"
    ]

    for field in required_fields:
        if not data.get(field):
            return {
                "success": False,
                "message": f"{field} is required."
            }

    role = data.get("role", "PATIENT").upper()

    if role not in ["ADMIN", "DONOR", "PATIENT", "HOSPITAL"]:
        return {
            "success": False,
            "message": "Invalid role."
        }
    
    if role == "HOSPITAL":
        hospital_fields = [
            "hospital_name",
            "address",
            "latitude",
            "longitude",
            "city",
            "state",
            "pincode"
        ]

        for field in hospital_fields:
            if not data.get(field):
                return {
                    "success": False,
                    "message": f"{field} is required for hospital registration."
                }
    if User.query.filter_by(email=data["email"]).first():
        return {
            "success": False,
            "message": "Email already exists."
        }

    if User.query.filter_by(phone=data["phone"]).first():
        return {
            "success": False,
            "message": "Phone number already exists."
        }

    try:
        # create user with hashed password and unverified email
        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            password=hash_password(data["password"]),
            role=role,
            active=True,
            is_email_verified=False
        )

        db.session.add(user)
        db.session.flush()

        if role == "DONOR":
            donor = Donor(
                user_id=user.user_id,
                blood_group=data.get("blood_group"),
                age=data.get("age"),
                gender=data.get("gender"),
                weight=data.get("weight"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                address=data.get("address"),
                availability=True,
                total_donations=0,
                reliability_score=0,
                reward_points=0,
                badge="New Donor"
            )
            db.session.add(donor)

        if role == "PATIENT":
            patient = Patient(user_id=user.user_id)
            db.session.add(patient)
        if role == "HOSPITAL":
            required_hospital_fields = [
                "hospital_name",
                "address",
                "latitude",
                "longitude"
            ]

            for field in required_hospital_fields:
                if data.get(field) is None or data.get(field) == "":
                    db.session.rollback()

                    return {
                        "success": False,
                        "message": f"{field} is required for hospital registration."
                    }

            hospital = Hospital(
                user_id=user.user_id,
                hospital_name=data.get("hospital_name"),
                address=data.get("address"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                phone=data.get("hospital_phone") or data.get("phone"),
                email=data.get("hospital_email") or data.get("email"),
                city=data.get("city"),
                state=data.get("state"),
                pincode=data.get("pincode"),
                is_active=True
            )

            db.session.add(hospital)

        # =====================================
        # CREATE OTP
        # =====================================
        otp = generate_verification_code()

        # Delete previous OTP for same email
        PasswordReset.query.filter_by(
            email=user.email
        ).delete()

        reset_record = PasswordReset(
            email=user.email,
            otp=otp,
            verified=False
        )

        db.session.add(reset_record)

        # =====================================
        # SAVE EVERYTHING
        # =====================================
        db.session.commit()

        # Send OTP email
        send_verification_code(user.email, otp)

        return {
            "success": True,
            "message": "Registration Successful. Please verify your email.",
            "user": user.to_dict(),
            "verification_required": True,
            "verification_code": otp
        }

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }


def verify_email(data):

    email = (data or {}).get("email")
    otp = str((data or {}).get("otp", "")).strip()

    if not email or not otp:
        return {
            "success": False,
            "message": "Email and OTP are required."
        }

    # Check user
    user = User.query.filter_by(email=email).first()

    if user is None:
        return {
            "success": False,
            "message": "User not found."
        }

    # Get latest unverified OTP for this email
    reset_record = PasswordReset.query.filter_by(
        email=email,
        verified=False
    ).order_by(
        PasswordReset.reset_id.desc()
    ).first()

    if reset_record is None:
        return {
            "success": False,
            "message": "OTP not found. Please register again."
        }

    # Compare OTP
    if str(reset_record.otp).strip() != otp:
        return {
            "success": False,
            "message": "Invalid OTP."
        }

    # Mark email verified
    user.is_email_verified = True
    user.active = True

    # Mark OTP as used
    reset_record.verified = True

    db.session.commit()

    return {
        "success": True,
        "message": "Email verified successfully.",
        "user": user.to_dict()
    }

def login_user(data):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "success": False,
            "message": "Email and Password are required."
        }

    user = User.query.filter_by(email=email).first()
    if user is None:
        return {
            "success": False,
            "message": "Invalid Email."
        }

    if not user.active:
        return {
            "success": False,
            "message": "User account is inactive."
        }

    if not getattr(user, 'is_email_verified', False):
        return {
            "success": False,
            "message": "Email not verified. Please verify your email first."
        }

    if not verify_password(password, user.password):
        return {
            "success": False,
            "message": "Invalid Password."
        }

    token = generate_token(user)

    return {
        "success": True,
        "message": "Login Successful.",
        "token": token,
        "user": user.to_dict()
    }


def reset_donor_password(email, new_password):
    user = User.query.filter_by(email=email, role="DONOR").first()

    if not user:
        return False

    user.password = hash_password(new_password)
    db.session.commit()
    return True


def reset_password_request(data):
    # for forgot-password: create a reset OTP and send it
    email = (data or {}).get("email")
    if not email:
        return {"success": False, "message": "Email is required."}

    user = User.query.filter_by(email=email).first()
    if user is None:
        # Do not reveal whether email exists — return generic success for security
        return {"success": True, "message": "If an account with this email exists, an OTP has been sent."}

    otp = generate_verification_code()
    otp_hash = werkzeug_hash(otp)
    verification = EmailVerification.make_record(email=email, otp_hash=otp_hash, purpose="reset", ttl_minutes=15, user_id=user.user_id)
    db.session.add(verification)
    db.session.commit()

    send_verification_code(email, otp, subject="Reset your BloodNeed password")

    return {"success": True, "message": "If an account with this email exists, an OTP has been sent."}


def reset_password_confirm(data):
    # Accept email + otp + new_password
    email = (data or {}).get("email")
    otp = str((data or {}).get("otp", "")).strip()
    new_password = (data or {}).get("new_password")

    if not email or not otp or not new_password:
        return {"success": False, "message": "Email, OTP and new_password are required."}

    user = User.query.filter_by(email=email).first()
    if user is None:
        return {"success": False, "message": "Invalid request."}

    record = EmailVerification.query.filter_by(email=email, purpose="reset", used=False).order_by(EmailVerification.verification_id.desc()).first()
    if record is None:
        return {"success": False, "message": "Invalid or expired OTP."}

    if record.expires_at and datetime.utcnow() > record.expires_at:
        return {"success": False, "message": "OTP expired."}

    if not check_password_hash(record.otp_hash, otp):
        return {"success": False, "message": "Invalid OTP."}

    # update password
    user.password = hash_password(new_password)
    record.used = True
    record.used_at = datetime.utcnow()
    db.session.commit()

    return {"success": True, "message": "Password has been reset successfully."}


# backward-compatible wrappers used by routes
def reset_password_service(data):
    # existing routes call reset_password_service for forgot/reset flows
    # we infer intent from data content
    if data.get('new_password'):
        # treat as confirm reset
        return reset_password_confirm(data)
    else:
        return reset_password_request(data)