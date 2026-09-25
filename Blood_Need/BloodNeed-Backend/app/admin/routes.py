from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

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
    if not donors:
        return jsonify([]), 200

    from app.models.reward_point import RewardPoint
    from app.models.badge import Badge

    user_ids = [d.user_id for d in donors if d.user_id]
    donor_ids = [d.donor_id for d in donors]

    users = User.query.filter(User.user_id.in_(user_ids)).all() if user_ids else []
    user_map = {u.user_id: u for u in users}

    reward_sums = dict(
        db.session.query(
            RewardPoint.donor_id,
            func.coalesce(func.sum(RewardPoint.points), 0)
        )
        .filter(RewardPoint.donor_id.in_(donor_ids))
        .group_by(RewardPoint.donor_id)
        .all()
    ) if donor_ids else {}

    badge_rows = (
        db.session.query(Badge.donor_id, Badge.badge_name)
        .filter(Badge.donor_id.in_(donor_ids), Badge.is_active == True)
        .all()
    ) if donor_ids else []
    badge_map = {}
    for did, bname in badge_rows:
        badge_map.setdefault(did, []).append(bname)

    return jsonify([
        donor.to_dict(
            user=user_map.get(donor.user_id),
            reward_points=int(reward_sums.get(donor.donor_id, 0)),
            badges=badge_map.get(donor.donor_id, [])
        )
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
    if not patients:
        return jsonify([]), 200

    user_ids = [p.user_id for p in patients if p.user_id]
    users = User.query.filter(User.user_id.in_(user_ids)).all() if user_ids else []
    user_map = {u.user_id: u for u in users}

    return jsonify([
        patient.to_dict(user=user_map.get(patient.user_id))
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

    from app.models.donor import Donor
    from app.models.patient import Patient
    from app.models.blood_request import BloodRequest
    from app.models.donation import Donation

    request_counts = dict(
        db.session.query(
            BloodRequest.status,
            func.count(BloodRequest.request_id)
        )
        .group_by(BloodRequest.status)
        .all()
    )

    return jsonify({
        "users": User.query.count(),
        "donors": Donor.query.count(),
        "patients": Patient.query.count(),
        "requests": sum(request_counts.values()),
        "pending_requests": request_counts.get("Pending", 0),
        "matched_requests": request_counts.get("Matched", 0),
        "accepted_requests": request_counts.get("Accepted", 0),
        "completed_requests": request_counts.get("Completed", 0),
        "cancelled_requests": request_counts.get("Cancelled", 0),
        "total_donations": Donation.query.count()
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