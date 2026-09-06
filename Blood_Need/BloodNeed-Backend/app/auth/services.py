import random
from datetime import datetime, timedelta

from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash as werkzeug_hash

from app import db
from app.auth.utils import hash_password, verify_password, generate_token
from app.models.donor import Donor
from app.models.password_reset import PasswordReset
from app.models.patient import Patient
from app.models.user import User
from app.models.hospital import Hospital
from app.models.email_verification import EmailVerification


def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_code(email, otp):
    try:
        from app.utils.email_service import send_email

        send_email(
            receiver=email,
            otp=otp,
            subject="BloodNeed - Email Verification OTP"
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
    if role == "HOSPITAL":

        hospital_required_fields = [
            "hospital_name",
            "address",
            "latitude",
            "longitude"
        ]

        for field in hospital_required_fields:
            if data.get(field) is None or data.get(field) == "":
                return {
                    "success": False,
                    "message": f"{field} is required for hospital registration."
                }

    if role not in ["ADMIN", "DONOR", "PATIENT", "HOSPITAL"]:
        return {
            "success": False,
            "message": "Invalid role."
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
        # =====================================
        # CREATE HOSPITAL PROFILE
        # =====================================
        if role == "HOSPITAL":

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

        otp = generate_verification_code()
        reset_record = PasswordReset(email=user.email, otp=otp, verified=False)
        db.session.add(reset_record)
        db.session.commit()

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
            "message": str(e)
        }


def verify_email(data):
    email = (data or {}).get("email")
    otp = str((data or {}).get("otp", "")).strip()

    if not email or not otp:
        return {"success": False, "message": "Email and OTP are required."}

    user = User.query.filter_by(email=email).first()
    if user is None:
        return {"success": False, "message": "User not found."}

    reset_record = PasswordReset.query.filter_by(email=email, otp=otp).order_by(PasswordReset.reset_id.desc()).first()
    if reset_record is None:
        return {"success": False, "message": "Invalid OTP."}

    user.is_email_verified = True
    user.active = True
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

    if not user.is_email_verified:
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


def reset_password(data):
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"message": "Email not found"}), 404

    user.password = generate_password_hash(password)
    db.session.commit()

    return jsonify({"message": "Password Updated Successfully"}), 200
