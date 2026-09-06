from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta


def hash_password(password):
    """
    Hash plain text password
    """
    return generate_password_hash(password)


def verify_password(password, hashed_password):
    """
    Verify password
    """
    return check_password_hash(hashed_password, password)


def generate_token(user):
    """
    Generate JWT access token
    """

    additional_claims = {
        "role": user.role,
        "email": user.email
    }

    token = create_access_token(
        identity=str(user.user_id),
        additional_claims=additional_claims,
        expires_delta=timedelta(days=1)
    )

    return token