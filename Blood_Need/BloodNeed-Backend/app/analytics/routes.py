from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.blood_request import BloodRequest
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.donation import Donation

from app.analytics.services import (
    blood_group_statistics,
    donor_availability_statistics,
    emergency_statistics,
    matching_statistics,
    donation_statistics
)

analytics_bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/analytics"
)


# ====================================================
# BLOOD GROUP STATISTICS
# ====================================================

@analytics_bp.route("/blood-groups", methods=["GET"])
@jwt_required()
def blood_groups():

    return jsonify(
        blood_group_statistics()
    ), 200


# ====================================================
# DONOR AVAILABILITY
# ====================================================

@analytics_bp.route("/donor-availability", methods=["GET"])
@jwt_required()
def donor_availability():

    return jsonify(
        donor_availability_statistics()
    ), 200


# ====================================================
# EMERGENCY LEVEL STATISTICS
# ====================================================

@analytics_bp.route("/emergency-levels", methods=["GET"])
@jwt_required()
def emergency_levels():

    return jsonify(
        emergency_statistics()
    ), 200


# ====================================================
# MATCHING STATISTICS
# ====================================================

@analytics_bp.route("/matches", methods=["GET"])
@jwt_required()
def matches():

    return jsonify(
        matching_statistics()
    ), 200


# ====================================================
# DONATION STATISTICS
# ====================================================

@analytics_bp.route("/donations", methods=["GET"])
@jwt_required()
def donations():

    return jsonify(
        donation_statistics()
    ), 200
# ====================================================
# ANALYTICS DASHBOARD
# ====================================================

from app.models.blood_request import BloodRequest
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.donation import Donation


@analytics_bp.route("/", methods=["GET"])
@jwt_required()
def analytics_dashboard():
    from app import db
    from sqlalchemy import func

    request_counts = dict(
        db.session.query(
            BloodRequest.status,
            func.count(BloodRequest.request_id)
        )
        .group_by(BloodRequest.status)
        .all()
    )
    total_requests = sum(request_counts.values())
    completed_requests = request_counts.get("Completed", 0)
    pending_requests = request_counts.get("Pending", 0)

    donor_counts = dict(
        db.session.query(
            Donor.availability,
            func.count(Donor.donor_id)
        )
        .group_by(Donor.availability)
        .all()
    )
    total_donors = sum(donor_counts.values())
    available_donors = donor_counts.get(True, 0)

    total_patients = Patient.query.count()
    total_donations = Donation.query.count()

    success_rate = 0

    if total_requests > 0:
        success_rate = round(
            (completed_requests / total_requests) * 100,
            2
        )

    return jsonify({

        "total_donations": total_donations,

        "total_requests": total_requests,

        "completed_requests": completed_requests,

        "pending_requests": pending_requests,

        "available_donors": available_donors,

        "total_donors": total_donors,

        "total_patients": total_patients,

        "success_rate": success_rate

    }), 200