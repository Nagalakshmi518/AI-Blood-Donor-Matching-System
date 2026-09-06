from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from app.auth.services_impl import (
    register_user,
    login_user,
    reset_password_service,
    verify_email,
)

from app.models.user import User

from app import db

from app.auth.utils import (
    hash_password,
    verify_password
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


# ====================================================
# REGISTER USER
# ====================================================

@auth_bp.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Registration data is required"
        }), 400

    result = register_user(data)

    if result["success"]:
        return jsonify(result), 201

    return jsonify(result), 400


# ====================================================
# LOGIN USER
# ====================================================

@auth_bp.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Login data is required"

        }), 400


    result = login_user(data)


    if result["success"]:

        return jsonify(result), 200


    return jsonify(result), 401


# ====================================================
# GET LOGGED-IN USER PROFILE
# ====================================================

@auth_bp.route(
    "/verify-email",
    methods=["POST"]
)
def verify_email_route():
    data = request.get_json() or {}
    if not data:
        return jsonify({"message": "Email and OTP are required."}), 400

    result = verify_email(data)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@auth_bp.route(
    "/profile",
    methods=["GET"]
)
@jwt_required()
def profile():

    user_id = get_jwt_identity()


    user = User.query.get(
        user_id
    )


    if user is None:

        return jsonify({

            "message":
                "User not found"

        }), 404


    return jsonify(

        user.to_dict()

    ), 200


# ====================================================
# CHANGE PASSWORD
# ====================================================

@auth_bp.route(
    "/change-password",
    methods=["PUT"]
)
@jwt_required()
def change_password():

    user_id = get_jwt_identity()


    user = User.query.get(
        user_id
    )


    if user is None:

        return jsonify({

            "message":
                "User not found"

        }), 404


    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Password data is required"

        }), 400


    current_password = data.get(
        "current_password"
    )


    new_password = data.get(
        "new_password"
    )


    if not current_password or not new_password:

        return jsonify({

            "message":
                "Current password and new password are required"

        }), 400


    if not verify_password(

        current_password,

        user.password

    ):

        return jsonify({

            "message":
                "Current password is incorrect"

        }), 400


    if len(new_password) < 6:

        return jsonify({

            "message":
                "New password must contain at least 6 characters"

        }), 400


    user.password = hash_password(

        new_password

    )


    db.session.commit()


    return jsonify({

        "message":
            "Password changed successfully"

    }), 200


# ====================================================
# RESET PASSWORD
# ====================================================

@auth_bp.route(
    "/reset-password",
    methods=["PUT"]
)
def reset_password():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    result = reset_password_service(data)

    status_code = result.get(
        "status_code",
        200 if result.get("success") else 400
    )

    return jsonify(result), status_code


# ====================================================
# RESET DONOR PASSWORD
# ====================================================

@auth_bp.route(
    "/reset-donor-password",
    methods=["POST"]
)
def reset_donor_password():

    data = request.get_json()


    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    email = data.get(
        "email"
    )


    new_password = data.get(
        "new_password"
    )


    if not email or not new_password:

        return jsonify({

            "message":
                "Email and new password are required"

        }), 400


    if len(new_password) < 6:

        return jsonify({

            "message":
                "New password must contain at least 6 characters"

        }), 400


    user = User.query.filter_by(

        email=email,

        role="DONOR"

    ).first()


    if user is None:

        return jsonify({

            "message":
                "Donor not found"

        }), 404


    user.password = hash_password(

        new_password

    )


    db.session.commit()


    return jsonify({

        "message":
            "Donor password reset successfully"

    }), 200
# ============================
# FORGOT PASSWORD
# ============================

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot():

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Reset password data is required"

        }), 400


    result = reset_password_service(data)

    status_code = result.get(
        "status_code",
        200 if result.get("success") else 400
    )

    return jsonify(result), status_code
