from re import match
from unittest import result

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

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


# -----------------------------
# Get All Patients
# -----------------------------
@patient_bp.route("/", methods=["GET"])
@jwt_required()
def patients():

    patients = get_all_patients()

    return jsonify([
        patient.to_dict()
        for patient in patients
    ])


# -----------------------------
# Get Patient By ID
# -----------------------------
@patient_bp.route("/<int:patient_id>", methods=["GET"])
@jwt_required()
def patient(patient_id):

    patient = get_patient(patient_id)

    if patient is None:
        return jsonify({
            "message": "Patient not found"
        }), 404

    return jsonify(patient.to_dict())


# -----------------------------
# Add Patient
# -----------------------------
@patient_bp.route("/", methods=["POST"])
@jwt_required()
def add_patient():

    data = request.get_json()
    user_id = get_jwt_identity()

    data["user_id"] = user_id

    valid, message = validate_patient(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400
    

    patient = create_patient(data)

    return jsonify(patient.to_dict()), 201


# -----------------------------
# Update Patient
# -----------------------------
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


# -----------------------------
# Delete Patient
# -----------------------------
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
# Logged-in Patient Dashboard
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

    total_requests = BloodRequest.query.filter_by(
        patient_id=patient.patient_id
    ).count()

    pending = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Pending"
    ).count()

    completed = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Completed"
    ).count()

    accepted = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Accepted"
    ).count()

    rejected = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Rejected"
    ).count()

    cancelled = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Cancelled"
    ).count()

    matched = BloodRequest.query.filter_by(
        patient_id=patient.patient_id,
        status="Matched"
    ).count()

    recent_requests = BloodRequest.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(
        BloodRequest.request_time.desc()
    ).limit(5).all()

    activities = []

    for req in recent_requests:

        activity = "Blood request created"

        if req.status == "Matched":
            activity = "AI matched donors"

        elif req.status == "Accepted":
            activity = "A donor accepted your request"

        elif req.status == "Rejected":
            activity = "Donor rejected your request"

        elif req.status == "Completed":
            activity = "Blood donation completed"

        elif req.status == "Cancelled":
            activity = "Request cancelled"

        activities.append({
            "request_id": req.request_id,
            "activity": activity,
            "blood_group": req.blood_group,
            "hospital": req.hospital_name,
            "status": req.status,
            "emergency_level": req.emergency_level,
            "request_time": req.request_time.strftime("%Y-%m-%d %H:%M:%S") if req.request_time else None
        })

    return jsonify({
        "patient": patient.to_dict(),
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
    })


# ====================================================
# Get Current Logged-in Patient Profile
# ====================================================
@patient_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_patient():
    """
    Get the logged-in patient's profile data.
    Returns patient details including blood_group, age, gender, hospital_name, etc.
    """
    user_id = get_jwt_identity()

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
    """
    Update the logged-in patient's profile data.
    Only allows updating: blood_group, age, gender, hospital_name, latitude, longitude
    """
    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    data = request.get_json()

    # Only allow updating specific fields
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
        print(f"Error updating patient: {str(e)}")
        return jsonify({
            "message": "Failed to update profile"
        }), 500

# ====================================================
# Logged-in Patient Requests
# ====================================================
# ====================================================
# Logged-in Patient Requests
# ====================================================
@patient_bp.route("/requests", methods=["GET"])
@jwt_required()
def patient_requests():

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404


    blood_requests = BloodRequest.query.filter_by(
        patient_id=patient.patient_id
    ).order_by(
        BloodRequest.request_id.desc()
    ).all()


    result = []


    for blood_request in blood_requests:

        request_data = blood_request.to_dict()

        matches = DonorMatch.query.filter_by(
            request_id=blood_request.request_id
        ).order_by(
            DonorMatch.ranking_score.desc()
        ).all()

        matched_donors = []

        for match in matches:

            donor = Donor.query.get(match.donor_id)

            if donor is None:
                continue

            matched_donors.append(
                donor.to_public_dict(
                    distance_km=match.distance_km,
                    ranking_score=match.ranking_score,
                    donor_response=match.donor_response,
                    response_probability=match.response_probability,
                    include_private=(match.donor_response == "Accepted")
                )
            )

        request_data["matched_donors"] = matched_donors
        request_data["matched_donors_count"] = len(matched_donors)
        accepted = next(
            (
                donor
                for donor in matched_donors
                if donor["donor_response"] == "Accepted"
            ),
            None
        )

        request_data["accepted_donor"] = accepted
        result.append(request_data)

    return jsonify(result), 200