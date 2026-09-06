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

    total_requests = BloodRequest.query.count()

    completed_requests = BloodRequest.query.filter_by(
        status="Completed"
    ).count()

    pending_requests = BloodRequest.query.filter_by(
        status="Pending"
    ).count()

    available_donors = Donor.query.filter_by(
        availability=True
    ).count()

    total_donors = Donor.query.count()

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