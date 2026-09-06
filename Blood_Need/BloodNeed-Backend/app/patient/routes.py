from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.blood_request import BloodRequest
from app.models.patient import Patient
from app.models.donor_match import DonorMatch
from app.models.donor import Donor
from app.models.user import User

from app.patient.services import (
    create_patient,
    get_all_patients,
    get_patient,
    update_patient,
    delete_patient
)

from app.schemas.patient_schema import validate_patient


patient_bp = Blueprint(
    "patient",
    __name__,
    url_prefix="/api/patients"
)


# ====================================================
# Get All Patients
# ====================================================
@patient_bp.route("/", methods=["GET"])
@jwt_required()
def patients():

    patients = get_all_patients()

    return jsonify([
        patient.to_dict()
        for patient in patients
    ])


# ====================================================
# Get Patient By ID
# ====================================================
@patient_bp.route("/<int:patient_id>", methods=["GET"])
@jwt_required()
def patient(patient_id):

    patient = get_patient(patient_id)

    if patient is None:
        return jsonify({
            "message": "Patient not found"
        }), 404

    return jsonify(patient.to_dict())


# ====================================================
# Add Patient
# ====================================================
@patient_bp.route("/", methods=["POST"])
@jwt_required()
def add_patient():

    data = request.get_json() or {}

    user_id = int(get_jwt_identity())

    data["user_id"] = user_id

    valid, message = validate_patient(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    patient = create_patient(data)

    return jsonify(patient.to_dict()), 201


# ====================================================
# Update Patient
# ====================================================
@patient_bp.route("/<int:patient_id>", methods=["PUT"])
@jwt_required()
def edit_patient(patient_id):

    patient = get_patient(patient_id)

    if patient is None:
        return jsonify({
            "message": "Patient not found"
        }), 404

    patient = update_patient(
        patient,
        request.get_json()
    )

    return jsonify(patient.to_dict())


# ====================================================
# Delete Patient
# ====================================================
@patient_bp.route("/<int:patient_id>", methods=["DELETE"])
@jwt_required()
def remove_patient(patient_id):

    patient = get_patient(patient_id)

    if patient is None:
        return jsonify({
            "message": "Patient not found"
        }), 404

    delete_patient(patient)

    return jsonify({
        "message": "Patient deleted successfully"
    })


# ====================================================
# Logged-in Patient Dashboard - OPTIMIZED
# ====================================================
@patient_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def patient_dashboard():

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404


    # ================================================
    # OPTIMIZATION:
    # Get all status counts in ONE database query
    # ================================================
    status_counts = (
        db.session.query(
            BloodRequest.status,
            func.count(BloodRequest.request_id)
        )
        .filter(
            BloodRequest.patient_id == patient.patient_id
        )
        .group_by(
            BloodRequest.status
        )
        .all()
    )

    statistics_map = {
        status: count
        for status, count in status_counts
    }

    total_requests = sum(statistics_map.values())

    pending = statistics_map.get("Pending", 0)
    matched = statistics_map.get("Matched", 0)
    accepted = statistics_map.get("Accepted", 0)
    completed = statistics_map.get("Completed", 0)
    rejected = statistics_map.get("Rejected", 0)
    cancelled = statistics_map.get("Cancelled", 0)


    # ================================================
    # Recent 5 requests
    # ================================================
    recent_requests = (
        BloodRequest.query
        .filter_by(patient_id=patient.patient_id)
        .order_by(BloodRequest.request_time.desc())
        .limit(5)
        .all()
    )


    activities = []

    activity_messages = {
        "Matched": "AI matched donors",
        "Accepted": "A donor accepted your request",
        "Rejected": "Donor rejected your request",
        "Completed": "Blood donation completed",
        "Cancelled": "Request cancelled"
    }

    for req in recent_requests:

        activity = activity_messages.get(
            req.status,
            "Blood request created"
        )

        activities.append({
            "request_id": req.request_id,
            "activity": activity,
            "blood_group": req.blood_group,
            "hospital": req.hospital_name,
            "status": req.status,
            "emergency_level": req.emergency_level,
            "request_time": (
                req.request_time.strftime("%Y-%m-%d %H:%M:%S")
                if req.request_time
                else None
            )
        })


    # Avoid patient.to_dict() extra query
    user = User.query.get(patient.user_id)

    patient_data = {
        "patient_id": patient.patient_id,
        "user_id": patient.user_id,
        "full_name": user.full_name if user else None,
        "phone": user.phone if user else None,
        "email": user.email if user else None,
        "blood_group": patient.blood_group,
        "age": patient.age,
        "gender": patient.gender,
        "hospital_name": patient.hospital_name,
        "latitude": patient.latitude,
        "longitude": patient.longitude
    }


    return jsonify({
        "patient": patient_data,

        "statistics": {
            "total_requests": total_requests,
            "pending": pending,
            "matched": matched,
            "accepted": accepted,
            "completed": completed,
            "rejected": rejected,
            "cancelled": cancelled
        },

        "recent_activities": activities
    }), 200


# ====================================================
# Get Current Logged-in Patient Profile
# ====================================================
@patient_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_patient():

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    return jsonify(patient.to_dict()), 200


# ====================================================
# Update Current Logged-in Patient Profile
# ====================================================
@patient_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_current_patient():

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    data = request.get_json() or {}

    allowed_fields = [
        "blood_group",
        "age",
        "gender",
        "hospital_name",
        "latitude",
        "longitude"
    ]

    for field in allowed_fields:
        if field in data:
            setattr(patient, field, data[field])

    try:
        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "patient": patient.to_dict()
        }), 200

    except Exception as e:

        db.session.rollback()

        print(
            f"Error updating patient: {str(e)}"
        )

        return jsonify({
            "message": "Failed to update profile"
        }), 500


# ====================================================
# Logged-in Patient Requests - HIGHLY OPTIMIZED
# ====================================================
@patient_bp.route("/requests", methods=["GET"])
@jwt_required()
def patient_requests():

    user_id = int(get_jwt_identity())


    # Get patient
    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404


    # ================================================
    # QUERY 1: Get all patient requests
    # ================================================
    blood_requests = (
        BloodRequest.query
        .filter_by(patient_id=patient.patient_id)
        .order_by(BloodRequest.request_id.desc())
        .all()
    )

    if not blood_requests:
        return jsonify([]), 200


    # Get all request IDs
    request_ids = [
        req.request_id
        for req in blood_requests
    ]


    # ================================================
    # QUERY 2: Get ALL matches at once
    # Instead of one query per request
    # ================================================
    all_matches = (
        DonorMatch.query
        .filter(
            DonorMatch.request_id.in_(request_ids)
        )
        .order_by(
            DonorMatch.ranking_score.desc()
        )
        .all()
    )


    # Group matches by request_id
    matches_by_request = {}

    donor_ids = set()

    for match in all_matches:

        matches_by_request.setdefault(
            match.request_id,
            []
        ).append(match)

        donor_ids.add(match.donor_id)


    # ================================================
    # QUERY 3: Get ALL donors at once
    # ================================================
    donors = []

    if donor_ids:
        donors = (
            Donor.query
            .filter(
                Donor.donor_id.in_(donor_ids)
            )
            .all()
        )


    donor_map = {
        donor.donor_id: donor
        for donor in donors
    }


    # ================================================
    # QUERY 4: Get ALL users at once
    # Avoid User.query.get() inside loop
    # ================================================
    user_ids = {
        donor.user_id
        for donor in donors
    }

    users = []

    if user_ids:
        users = (
            User.query
            .filter(
                User.user_id.in_(user_ids)
            )
            .all()
        )


    user_map = {
        user.user_id: user
        for user in users
    }


    # ================================================
    # Build response without extra DB queries
    # ================================================
    result = []


    for blood_request in blood_requests:

        request_data = blood_request.to_dict()

        request_matches = matches_by_request.get(
            blood_request.request_id,
            []
        )

        matched_donors = []


        for match in request_matches:

            donor = donor_map.get(
                match.donor_id
            )

            if donor is None:
                continue


            user = user_map.get(
                donor.user_id
            )


            donor_data = {

                "donor_id": donor.donor_id,

                "full_name": (
                    user.full_name
                    if user
                    else "Unknown Donor"
                ),

                "blood_group": donor.blood_group,

                "availability": donor.availability,

                "distance_km": (
                    round(match.distance_km, 2)
                    if match.distance_km is not None
                    else None
                ),

                "ranking_score": (
                    round(match.ranking_score, 2)
                    if match.ranking_score is not None
                    else None
                ),

                "response_probability": (
                    round(match.response_probability, 2)
                    if match.response_probability is not None
                    else None
                ),

                "reliability_score": (
                    round(donor.reliability_score, 2)
                    if donor.reliability_score is not None
                    else None
                ),

                "donor_response": (
                    match.donor_response
                    or "Pending"
                ),

                "match_status": (
                    match.donor_response
                    or "Pending"
                )
            }


            # Show private contact details ONLY
            # after donor accepts
            if match.donor_response == "Accepted":

                donor_data["phone"] = (
                    user.phone
                    if user
                    else None
                )

                donor_data["email"] = (
                    user.email
                    if user
                    else None
                )


            matched_donors.append(
                donor_data
            )


        request_data["matched_donors"] = (
            matched_donors
        )

        request_data["matched_donors_count"] = (
            len(matched_donors)
        )


        accepted_donor = next(
            (
                donor
                for donor in matched_donors
                if donor["donor_response"] == "Accepted"
            ),
            None
        )


        request_data["accepted_donor"] = (
            accepted_donor
        )


        result.append(
            request_data
        )


    return jsonify(result), 200