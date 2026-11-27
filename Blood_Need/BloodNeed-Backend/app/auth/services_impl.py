import math
import random
import re
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
        print("CALLING EMAIL SERVICE:", email, otp)
        send_email(
            receiver=email,
            otp=otp,
            subject=subject or "BloodNeed OTP"
        )
        print("EMAIL SERVICE RETURNED SUCCESS")

        return True

    except Exception as e:
        print("Email sending error:", e)
        return False


def _is_valid_phone(phone_value, max_length=20):
    raw = str(phone_value or "").strip()
    if not raw or len(raw) > max_length:
        return False
    if not re.fullmatch(r"[+\d\s()-]+", raw):
        return False
    digits = re.sub(r"\D", "", raw)
    return 7 <= len(digits) <= 15


def _parse_coordinate(value, min_val, max_val):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < min_val or parsed > max_val:
        return None
    return parsed


def register_user(data):
    required_fields = [
        "full_name",
        "email",
        "phone",
        "password"
    ]

    for field in required_fields:
        val = data.get(field)
        if val is None or str(val).strip() == "":
            return {
                "success": False,
                "field": field,
                "message": f"{field} is required."
            }

    full_name = str(data.get("full_name")).strip()
    email = str(data.get("email")).strip()
    phone = str(data.get("phone")).strip()
    password = str(data.get("password"))

    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return {
            "success": False,
            "field": "email",
            "message": "Please enter a valid email address."
        }

    if not _is_valid_phone(phone, max_length=20):
        return {
            "success": False,
            "field": "phone",
            "message": "Please enter a valid phone number (7-15 digits)."
        }

    if len(password) < 6:
        return {
            "success": False,
            "field": "password",
            "message": "Password must be at least 6 characters long."
        }

    role = str(data.get("role", "PATIENT")).strip().upper()

    if role not in ["ADMIN", "DONOR", "PATIENT", "HOSPITAL"]:
        return {
            "success": False,
            "field": "role",
            "message": "Invalid role."
        }

    hospital_name = None
    hospital_address = None
    hospital_city = None
    hospital_state = None
    hospital_phone = None
    hospital_email = None
    hospital_pincode = None
    hospital_lat = None
    hospital_lng = None

    if role == "HOSPITAL":
        hospital_name = str(data.get("hospital_name") or "").strip()
        hospital_address = str(data.get("address") or data.get("hospital_address") or "").strip()
        hospital_city = str(data.get("city") or data.get("hospital_city") or "").strip()
        hospital_state = str(data.get("state") or data.get("hospital_state") or "").strip()
        hospital_phone = str(data.get("hospital_phone") or phone).strip()
        hospital_email = str(data.get("hospital_email") or email).strip()
        raw_pincode = data.get("pincode")
        hospital_pincode = str(raw_pincode).strip() if raw_pincode is not None and str(raw_pincode).strip() != "" else None

        required_hospital_values = [
            ("hospital_name", hospital_name),
            ("address", hospital_address),
            ("city", hospital_city),
            ("state", hospital_state),
        ]
        for field_name, field_val in required_hospital_values:
            if not field_val:
                return {
                    "success": False,
                    "field": field_name,
                    "message": f"{field_name} is required for hospital registration."
                }

        if not _is_valid_phone(hospital_phone, max_length=15):
            return {
                "success": False,
                "field": "hospital_phone",
                "message": "Please enter a valid hospital desk phone number (7-15 digits, max 15 characters)."
            }

        if hospital_pincode is not None and len(hospital_pincode) > 10:
            return {
                "success": False,
                "field": "pincode",
                "message": "Pincode must be 10 characters or fewer."
            }

        raw_lat = data.get("latitude")
        if raw_lat is None or (isinstance(raw_lat, str) and raw_lat.strip() == ""):
            return {
                "success": False,
                "field": "latitude",
                "message": "latitude is required for hospital registration."
            }
        hospital_lat = _parse_coordinate(raw_lat, -90.0, 90.0)
        if hospital_lat is None:
            return {
                "success": False,
                "field": "latitude",
                "message": "Hospital latitude must be a valid number between -90 and 90."
            }

        raw_lng = data.get("longitude")
        if raw_lng is None or (isinstance(raw_lng, str) and raw_lng.strip() == ""):
            return {
                "success": False,
                "field": "longitude",
                "message": "longitude is required for hospital registration."
            }
        hospital_lng = _parse_coordinate(raw_lng, -180.0, 180.0)
        if hospital_lng is None:
            return {
                "success": False,
                "field": "longitude",
                "message": "Hospital longitude must be a valid number between -180 and 180."
            }

    existing_user = User.query.filter(
        (User.email == email) | (User.phone == phone)
    ).first()

    if existing_user:
        if existing_user.email == email:
            return {
                "success": False,
                "field": "email",
                "message": "Email already exists."
            }
        return {
            "success": False,
            "field": "phone",
            "message": "Phone number already exists."
        }

    try:
        # create user with hashed password and unverified email
        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hash_password(password),
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
            hospital = Hospital(
                user_id=user.user_id,
                hospital_name=hospital_name,
                address=hospital_address,
                latitude=hospital_lat,
                longitude=hospital_lng,
                phone=hospital_phone,
                email=hospital_email,
                city=hospital_city,
                state=hospital_state,
                pincode=hospital_pincode,
                is_active=True
            )

            db.session.add(hospital)

        # =====================================
        # CREATE OTP
        # =====================================
        otp = generate_verification_code()
        print("GENERATED OTP:", otp)
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
    print("VERIFY EMAIL:", repr(email))
    print("VERIFY OTP:", repr(otp))

    if not email or not otp:
        return {
            "success": False,
            "message": "Email and OTP are required."
        }

    # Check user
    user = User.query.filter_by(email=email).first()
    print("VERIFY USER:", user)
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
    print("VERIFY OTP RECORD:", reset_record)
    if reset_record is None:
        return {
            "success": False,
            "message": "OTP not found. Please register again."
        }
    print("DB OTP:", repr(str(reset_record.otp).strip()))
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