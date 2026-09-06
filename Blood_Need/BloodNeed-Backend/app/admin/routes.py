from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db

from app.models.user import User

from app.admin.services import (
    get_admin_summary,
    get_all_users,
    get_all_donors,
    get_all_patients,
    get_all_blood_requests,
    get_all_donations,
    get_all_matches,
    delete_blood_request,
    delete_donor,
    delete_patient,
    delete_user,
    delete_donation,
    delete_match,
)

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


# ====================================================
# ADMIN AUTHORIZATION
# ====================================================

def check_admin():

    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)

    if user is None:
        return False

    if user.role != "ADMIN":
        return False

    return True


# ====================================================
# ADMIN DASHBOARD
# ====================================================

@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    return jsonify(
        get_admin_summary()
    ), 200


# ====================================================
# GET ALL USERS
# ====================================================

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def users():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    users = get_all_users()

    return jsonify([
        user.to_dict()
        for user in users
    ]), 200


# ====================================================
# GET ALL DONORS
# ====================================================

@admin_bp.route("/donors", methods=["GET"])
@jwt_required()
def donors():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    donors = get_all_donors()

    return jsonify([
        donor.to_dict()
        for donor in donors
    ]), 200


# ====================================================
# GET ALL PATIENTS
# ====================================================

@admin_bp.route("/patients", methods=["GET"])
@jwt_required()
def patients():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    patients = get_all_patients()

    return jsonify([
        patient.to_dict()
        for patient in patients
    ]), 200


# ====================================================
# GET ALL BLOOD REQUESTS
# ====================================================

@admin_bp.route("/requests", methods=["GET"])
@jwt_required()
def requests():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    requests = get_all_blood_requests()

    return jsonify([
        req.to_dict()
        for req in requests
    ]), 200


# ====================================================
# GET ALL DONATIONS
# ====================================================

@admin_bp.route("/donations", methods=["GET"])
@jwt_required()
def donations():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    donations = get_all_donations()

    return jsonify([
        donation.to_dict()
        for donation in donations
    ]), 200


# ====================================================
# GET ALL MATCHES
# ====================================================

@admin_bp.route("/matches", methods=["GET"])
@jwt_required()
def matches():

    if not check_admin():

        return jsonify({
            "message": "Admin access required"
        }), 403

    matches = get_all_matches()

    return jsonify([
        match.to_dict()
        for match in matches
    ]), 200
# ====================================================
# ADMIN ANALYTICS
# ====================================================

@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    from app.models.user import User
    from app.models.donor import Donor
    from app.models.patient import Patient
    from app.models.blood_request import BloodRequest
    from app.models.donation import Donation

    return jsonify({

        "users": User.query.count(),

        "donors": Donor.query.count(),

        "patients": Patient.query.count(),

        "requests": BloodRequest.query.count(),

        "pending_requests":
            BloodRequest.query.filter_by(
                status="Pending"
            ).count(),

        "matched_requests":
            BloodRequest.query.filter_by(
                status="Matched"
            ).count(),

        "accepted_requests":
            BloodRequest.query.filter_by(
                status="Accepted"
            ).count(),

        "completed_requests":
            BloodRequest.query.filter_by(
                status="Completed"
            ).count(),

        "cancelled_requests":
            BloodRequest.query.filter_by(
                status="Cancelled"
            ).count(),

        "total_donations":
            Donation.query.count()

    }), 200
# ====================================================
# BLOCK USER
# ====================================================

@admin_bp.route("/users/<int:user_id>/block", methods=["PATCH"])
@jwt_required()
def block_user(user_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({
            "message": "User not found"
        }), 404
    if user.user_id == get_jwt_identity():
        return jsonify({
            "message": "You cannot block your own account"
        }), 400

    user.active = False

    db.session.commit()

    return jsonify({
        "message": "User blocked successfully"
    }), 200


# ====================================================
# UNBLOCK USER
# ====================================================

@admin_bp.route("/users/<int:user_id>/unblock", methods=["PATCH"])
@jwt_required()
def unblock_user(user_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({
            "message": "User not found"
        }), 404

    user.active = True

    db.session.commit()

    return jsonify({
        "message": "User unblocked successfully"
    }), 200


# ====================================================
# DELETE BLOOD REQUEST
# ====================================================

@admin_bp.route("/requests/<int:request_id>", methods=["DELETE"])
@jwt_required()
def remove_request(request_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    if not delete_blood_request(request_id):
        return jsonify({
            "message": "Blood request not found"
        }), 404

    return jsonify({
        "message": "Blood request deleted successfully"
    }), 200


# ====================================================
# DELETE DONOR
# ====================================================

@admin_bp.route("/donors/<int:donor_id>", methods=["DELETE"])
@jwt_required()
def remove_donor(donor_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    if not delete_donor(donor_id):
        return jsonify({
            "message": "Donor not found"
        }), 404

    return jsonify({
        "message": "Donor deleted successfully"
    }), 200


# ====================================================
# DELETE PATIENT
# ====================================================

@admin_bp.route("/patients/<int:patient_id>", methods=["DELETE"])
@jwt_required()
def remove_patient(patient_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    if not delete_patient(patient_id):
        return jsonify({
            "message": "Patient not found"
        }), 404

    return jsonify({
        "message": "Patient deleted successfully"
    }), 200


# ====================================================
# DELETE USER
# ====================================================

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_user(user_id):

    if not check_admin():
        return jsonify({
            "message": "Admin access required"
        }), 403

    if user_id == get_jwt_identity():
        return jsonify({
            "message": "You cannot delete your own account"
        }), 400

    if not delete_user(user_id):
        return jsonify({
            "message": "User not found"
        }), 404

    return jsonify({
        "message": "User deleted successfully"
    }), 200
@admin_bp.route("/donations/<int:donation_id>", methods=["DELETE"])
@jwt_required()
def remove_donation(donation_id):

    if not check_admin():
        return jsonify({"message":"Admin access required"}),403

    if not delete_donation(donation_id):
        return jsonify({"message":"Donation not found"}),404

    return jsonify({"message":"Donation deleted successfully"}),200
@admin_bp.route("/matches/<int:match_id>", methods=["DELETE"])
@jwt_required()
def remove_match(match_id):

    if not check_admin():
        return jsonify({"message":"Admin access required"}),403

    if not delete_match(match_id):
        return jsonify({"message":"Match not found"}),404

    return jsonify({"message":"Match deleted successfully"}),200