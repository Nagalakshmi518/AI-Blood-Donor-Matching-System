from datetime import timedelta

from flask_jwt_extended import (
    create_access_token,
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, hashed_password):
    return check_password_hash(hashed_password, password)


def generate_token(user):
    return create_access_token(
        identity=str(user.user_id),
        additional_claims={
            "role": user.role,
            "email": user.email
        },
        expires_delta=timedelta(days=1)
    )