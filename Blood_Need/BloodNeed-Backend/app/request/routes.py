from urllib import response

from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from app import db

from app.models.patient import Patient
from app.models.donor_match import DonorMatch
from app.models.hospital_inventory import HospitalInventory
from app.matching.services import find_matching_donors
from app.notifications.services import create_notification

from app.request.services import (
    create_request,
    get_all_requests,
    get_request,
    update_request,
    delete_request,
    complete_request
)

from app.schemas.request_schema import validate_request


request_bp = Blueprint(
    "request",
    __name__,
    url_prefix="/api/requests"
)


# ====================================================
# GET MY BLOOD REQUESTS
# ====================================================
# ====================================================
# GET MY BLOOD REQUESTS
# ====================================================

@request_bp.route("/", methods=["GET"])
@jwt_required()
def requests():

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    all_requests = get_all_requests()

    patient_requests = [
        req
        for req in all_requests
        if req.patient_id == patient.patient_id
    ]

    response = []

    for req in patient_requests:

        request_data = req.to_dict()

        matches = DonorMatch.query.filter_by(
            request_id=req.request_id
        ).order_by(
            DonorMatch.ranking_score.desc()
        ).all()

        request_data["matched_donors"] = []

        for match in matches:

            donor = match.donor

            if donor is None:
                continue

            donor_data = donor.to_public_dict(
                distance_km=match.distance_km,
                ranking_score=match.ranking_score,
                donor_response=match.donor_response,
                response_probability=match.response_probability,
                include_private=(
                    match.donor_response == "Accepted"
                )
            )

            request_data["matched_donors"].append({
                "match_id": match.match_id,

                "donor": donor_data,

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

                "donor_response": match.donor_response,

                "response_deadline": (
                    match.response_deadline.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if match.response_deadline
                    else None
                )
            })

        # ====================================================
        # HOSPITAL INVENTORY STATUS
        # ====================================================

        inventory_records = HospitalInventory.query.filter_by(
            blood_group=req.blood_group
        ).order_by(
            HospitalInventory.available_units.desc()
        ).all()

        required_units = req.units_needed or 1

        total_available_units = sum(
            inventory.available_units or 0
            for inventory in inventory_records
        )

        accepted_exists = any(
            match.donor_response == "Accepted"
            for match in matches
        )

        active_pending_exists = any(
            match.donor_response == "Pending"
            for match in matches
        )

        all_donors_finished = (
            len(matches) > 0
            and all(
                match.donor_response in [
                    "Rejected",
                    "Missed",
                    "Expired"
                ]
                for match in matches
            )
        )

        # Inventory should be shown when:
        # 1. No accepted donor exists
        # 2. No active donor is waiting
        # 3. All donor attempts are finished
        # 4. Inventory exists for requested blood group

        inventory_fallback_active = (
            not accepted_exists
            and not active_pending_exists
            and all_donors_finished
        )

        request_data["hospital_inventory"] = {
            "blood_group": req.blood_group,
            "required_units": required_units,
            "available_units": total_available_units,
            "sufficient": (
                total_available_units >= required_units
            ),
            "fallback_active": inventory_fallback_active
        }

        request_data["inventory_fallback"] = (
            inventory_fallback_active
        )

        request_data["inventory_available_units"] = (
            total_available_units
        )

        request_data["inventory_used"] = (
            req.status == "Completed"
            and inventory_fallback_active
            and not accepted_exists
        )

        response.append(request_data)

    return jsonify(response), 200


# ====================================================
# GET SINGLE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["GET"]
)
@jwt_required()
def request_details(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    return jsonify(
        req.to_dict()
    ), 200


# ====================================================
# CREATE BLOOD REQUEST
# ====================================================

@request_bp.route("/", methods=["POST"])
@jwt_required()
def add_request():

    data = request.get_json()

    if not data:

        return jsonify({
            "message": "Request data is required"
        }), 400

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    # Automatically assign logged-in patient
    data["patient_id"] = patient.patient_id

    # Validate request data
    valid, message = validate_request(data)

    if not valid:

        return jsonify({
            "message": message
        }), 400

    # Create blood request
    req = create_request(data)

    if req is None:

        return jsonify({
            "message": "Failed to create blood request"
        }), 400

    # ====================================================
    # START AI MATCHING ONLY ONCE
    # ====================================================

    matches = find_matching_donors(req)

    if matches:

        req.status = "Matched"

        matching_status = "Matched"

        message = (
            "Blood request created successfully. "
            "Matching started and the top-ranked donor was notified."
        )

    else:
        from app.hospital.services import fallback_blood_bank_for_request

        fallback_used = fallback_blood_bank_for_request(req)
        req.status = "Completed" if fallback_used else "Pending"

        matching_status = "Completed" if fallback_used else "Pending"

        message = (
            "Blood request created successfully. "
            "No eligible donor was available; hospital inventory fallback was checked."
        )

    db.session.commit()

    return jsonify({

        "message": message,

        "request": req.to_dict(),

        "matching_status": matching_status,

        "donor_notified": len(matches) > 0

    }), 201


# ====================================================
# UPDATE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["PUT"]
)
@jwt_required()
def edit_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:

        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({
            "message": "Unauthorized"
        }), 403

    # Do not modify completed or accepted requests
    if req.status in [

        "Accepted",

        "Completed",

        "Cancelled"

    ]:

        return jsonify({

            "message":
                "This request cannot be modified now"

        }), 400

    data = request.get_json()

    if not data:

        return jsonify({

            "message":
                "Update data is required"

        }), 400

    # Validate updated data
    valid, message = validate_request({

        **data,

        "patient_id":
            patient.patient_id

    })

    if not valid:

        return jsonify({

            "message":
                message

        }), 400

    req = update_request(

        req,

        data

    )

    return jsonify(

        req.to_dict()

    ), 200


# ====================================================
# DELETE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>",
    methods=["DELETE"]
)
@jwt_required()
def remove_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status == "Completed":

        return jsonify({

            "message":
                "Completed request cannot be deleted"

        }), 400

    # Remove pending matches first
    DonorMatch.query.filter_by(

        request_id=req.request_id

    ).delete(

        synchronize_session=False

    )

    delete_request(req)

    return jsonify({

        "message":
            "Blood request deleted successfully"

    }), 200


# ====================================================
# CANCEL BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>/cancel",
    methods=["PATCH"]
)
@jwt_required()
def cancel_request(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status == "Cancelled":

        return jsonify({

            "message":
                "Request already cancelled"

        }), 400

    if req.status == "Completed":

        return jsonify({

            "message":
                "Completed request cannot be cancelled"

        }), 400

    # Cancel request
    req.status = "Cancelled"

    # Cancel all pending donor matches
    DonorMatch.query.filter_by(

        request_id=req.request_id,

        donor_response="Pending"

    ).update({

        "donor_response":
            "Rejected"

    })

    db.session.commit()

    return jsonify({

        "message":
            "Blood request cancelled successfully",

        "status":
            req.status

    }), 200


# ====================================================
# GET REQUEST STATUS
# ====================================================

@request_bp.route(
    "/<int:request_id>/status",
    methods=["GET"]
)
@jwt_required()
def request_status(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    return jsonify({

        "request_id":
            req.request_id,

        "status":
            req.status,

        "emergency_level":
            req.emergency_level

    }), 200

# ====================================================
# COMPLETE BLOOD REQUEST
# ====================================================
# ====================================================
# COMPLETE BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>/complete",
    methods=["PATCH"]
)
@jwt_required()
def complete_blood_request(request_id):

    req = get_request(request_id)

    if req is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:
        return jsonify({
            "message": "Unauthorized"
        }), 403

    if req.status == "Completed":
        return jsonify({
            "message": "Donation has already been completed."
        }), 400

    result = complete_request(request_id)

    if result is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    if result == "already_completed":
        return jsonify({
            "message": "Donation has already been completed."
        }), 400

    if result is False:
        return jsonify({
            "message": "No accepted donor found for this request"
        }), 400

    return jsonify({
        "message": "Blood request completed successfully",
        "status": result.status
    }), 200
# ====================================================
# MANUAL MATCHING
# ====================================================

@request_bp.route(
    "/<int:request_id>/match",
    methods=["POST"]
)
@jwt_required()
def trigger_matching(request_id):

    req = get_request(request_id)

    if req is None:

        return jsonify({

            "message":
                "Blood request not found"

        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(

        user_id=user_id

    ).first()

    if patient is None:

        return jsonify({

            "message":
                "Patient profile not found"

        }), 404

    if req.patient_id != patient.patient_id:

        return jsonify({

            "message":
                "Unauthorized"

        }), 403

    if req.status in [

        "Cancelled",

        "Completed",

        "Accepted"

    ]:

        return jsonify({

            "message":
                "Matching cannot be started for this request"

        }), 400

    # Check whether an active donor is already responding
    existing_pending_match = (

        DonorMatch.query.filter_by(

            request_id=request_id,

            donor_response="Pending"

        ).first()

    )

    if existing_pending_match:

        return jsonify({

            "message":
                "An active donor match already exists",

            "match_id":
                existing_pending_match.match_id

        }), 400

    # Start matching
    matches = find_matching_donors(req)

    if not matches:

        req.status = "Pending"

        db.session.commit()

        return jsonify({

            "message":
                "No eligible matching donors found",

            "status":
                req.status

        }), 404

    req.status = "Matched"

    db.session.commit()

    return jsonify({

        "message":
            "AI matching started successfully",

        "request_id":
            req.request_id,

        "donor_notified":
            True,

        "status":
            req.status

    }), 200
# ====================================================
# GET HOSPITAL INVENTORY FOR BLOOD REQUEST
# ====================================================

@request_bp.route(
    "/<int:request_id>/inventory",
    methods=["GET"]
)
@jwt_required()
def get_request_inventory(request_id):

    req = get_request(request_id)

    if req is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    user_id = get_jwt_identity()

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if patient is None:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    if req.patient_id != patient.patient_id:
        return jsonify({
            "message": "Unauthorized"
        }), 403

    inventory_records = HospitalInventory.query.filter_by(
        blood_group=req.blood_group
    ).order_by(
        HospitalInventory.available_units.desc()
    ).all()

    required_units = req.units_needed or 1

    total_available_units = sum(
        inventory.available_units or 0
        for inventory in inventory_records
    )

    return jsonify({
        "request_id": req.request_id,
        "blood_group": req.blood_group,
        "required_units": required_units,
        "available_units": total_available_units,
        "sufficient": total_available_units >= required_units,
        "inventory_found": len(inventory_records) > 0
    }), 200
