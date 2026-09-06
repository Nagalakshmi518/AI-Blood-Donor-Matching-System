from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.hospital.services import (
    create_hospital,
    get_all_hospitals,
    get_hospital,
    update_hospital,
    delete_hospital,
    get_inventory,
    add_units,
    use_units,
)
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.hospital_inventory import HospitalInventory
from app.models.blood_request import BloodRequest
from app.models.hospital import Hospital
from app.notifications.services import create_notification
from flask import abort

from app.schemas.hospital_schema import validate_hospital

hospital_bp = Blueprint(
    "hospital",
    __name__
)
@hospital_bp.route("/my-profile", methods=["GET"])
@jwt_required()
def get_my_hospital_profile():

    user_id = int(get_jwt_identity())

    hospital = Hospital.query.filter_by(
        user_id=user_id
    ).first()

    if not hospital:
        return jsonify({
            "success": False,
            "message": "Hospital profile not found."
        }), 404

    return jsonify({
        "success": True,
        "message": "Hospital profile fetched successfully.",
        "hospital": hospital.to_dict()
    }), 200
@hospital_bp.route("/", methods=["GET"])
@jwt_required()
def hospitals():

    hospitals = get_all_hospitals()

    return jsonify([
        hospital.to_dict()
        for hospital in hospitals
    ]),200
@hospital_bp.route("/<int:hospital_id>", methods=["GET"])
@jwt_required()
def hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    return jsonify(hospital.to_dict())


# -----------------------------
# Hospital Inventory Endpoints
# -----------------------------


def _require_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user is None or user.role != "ADMIN":
        abort(403)


@hospital_bp.route("/inventory", methods=["GET"])
@jwt_required()
def all_hospital_inventory():
    _require_admin()

    rows = []
    for hospital in get_all_hospitals():
        for item in get_inventory(hospital.hospital_id):
            payload = item.to_dict()
            payload["hospital_name"] = hospital.hospital_name
            rows.append(payload)

    return jsonify(rows), 200

@hospital_bp.route("/<int:hospital_id>/inventory", methods=["GET"])
@jwt_required()
def hospital_inventory(hospital_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    # ADMIN can view any hospital inventory
    if user.role == "ADMIN":
        pass

    # HOSPITAL can view only its own inventory
    elif user.role == "HOSPITAL":

        if hospital.user_id != user_id:
            return jsonify({
                "message": "You are not authorized to view this hospital inventory"
            }), 403

    else:
        return jsonify({
            "message": "Access denied"
        }), 403

    inv = get_inventory(hospital_id)

    return jsonify([
        item.to_dict()
        for item in inv
    ]), 200

@hospital_bp.route("/<int:hospital_id>/inventory/add", methods=["POST"])
@jwt_required()
def hospital_inventory_add(hospital_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    # ADMIN can update any hospital inventory
    if user.role == "ADMIN":
        pass

    # HOSPITAL can update only its own inventory
    elif user.role == "HOSPITAL":

        if hospital.user_id != user_id:
            return jsonify({
                "message": "You are not authorized to update this hospital inventory"
            }), 403

    else:
        return jsonify({
            "message": "Access denied"
        }), 403

    data = request.get_json() or {}

    blood_group = data.get("blood_group")
    units = data.get("units")

    if not blood_group or units is None:
        return jsonify({
            "message": "blood_group and units are required"
        }), 400

    try:
        units = int(units)
    except Exception:
        return jsonify({
            "message": "units must be an integer"
        }), 400

    if units <= 0:
        return jsonify({
            "message": "units must be greater than 0"
        }), 400

    try:
        inv = add_units(
            hospital_id,
            blood_group,
            units
        )

    except ValueError as e:
        return jsonify({
            "message": str(e)
        }), 400

    create_notification({
        "user_id": user_id,
        "title": "Hospital Inventory Updated",
        "message": f"{units} units of {blood_group} added to {hospital.hospital_name}",
        "notification_type": "INFO",
        "related_request_id": None,
        "is_read": False,
    })

    return jsonify({
        "success": True,
        "message": "Blood units added successfully",
        "inventory": inv.to_dict()
    }), 200
@hospital_bp.route("/<int:hospital_id>/inventory/use", methods=["POST"])
@jwt_required()
def hospital_inventory_use(hospital_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    # ADMIN can update any hospital inventory
    if user.role == "ADMIN":
        pass

    # HOSPITAL can update only its own inventory
    elif user.role == "HOSPITAL":

        if hospital.user_id != user_id:
            return jsonify({
                "message": "You are not authorized to update this hospital inventory"
            }), 403

    else:
        return jsonify({
            "message": "Access denied"
        }), 403

    data = request.get_json() or {}

    blood_group = data.get("blood_group")
    units = data.get("units")

    if not blood_group or units is None:
        return jsonify({
            "message": "blood_group and units are required"
        }), 400

    try:
        units = int(units)
    except Exception:
        return jsonify({
            "message": "units must be an integer"
        }), 400

    if units <= 0:
        return jsonify({
            "message": "units must be greater than 0"
        }), 400

    try:
        inv = use_units(
            hospital_id,
            blood_group,
            units
        )

    except ValueError as e:
        return jsonify({
            "message": str(e)
        }), 400

    create_notification({
        "user_id": user_id,
        "title": "Hospital Inventory Updated",
        "message": f"{units} units of {blood_group} used at {hospital.hospital_name}",
        "notification_type": "INFO",
        "related_request_id": None,
        "is_read": False,
    })

    return jsonify({
        "success": True,
        "message": "Blood units used successfully",
        "inventory": inv.to_dict()
    }), 200
@hospital_bp.route("/", methods=["POST"])
@jwt_required()
def add_hospital():
    
    data = request.get_json()

    valid, message = validate_hospital(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    hospital = create_hospital(data)

    return jsonify(hospital.to_dict()), 201
@hospital_bp.route("/<int:hospital_id>", methods=["PUT"])
@jwt_required()
def edit_hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    hospital = update_hospital(
        hospital,
        request.get_json()
    )

    return jsonify(hospital.to_dict())
@hospital_bp.route("/<int:hospital_id>", methods=["DELETE"])
@jwt_required()
def remove_hospital(hospital_id):

    hospital = get_hospital(hospital_id)

    if not hospital:
        return jsonify({
            "message": "Hospital not found"
        }), 404

    delete_hospital(hospital)

    return jsonify({
        "message": "Hospital deleted successfully"
    })
# =====================================================
# PATIENT REQUEST INVENTORY CHECK
# =====================================================

@hospital_bp.route("/request/<int:request_id>/inventory", methods=["GET"])
@jwt_required()
def request_inventory(request_id):

    user_id = get_jwt_identity()

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    # -------------------------------------------------
    # Only the patient who owns this request can view it
    # -------------------------------------------------

    patient = blood_request.patient

    if patient is None or patient.user_id != user_id:
        return jsonify({
            "message": "You are not authorized to view this request inventory"
        }), 403

    # -------------------------------------------------
    # Find hospital
    # -------------------------------------------------

    hospital = None

    if getattr(blood_request, "hospital_id", None):
        hospital = Hospital.query.get(
            blood_request.hospital_id
        )

    # Fallback: find by hospital name
    if hospital is None and blood_request.hospital_name:
        hospital = Hospital.query.filter_by(
            hospital_name=blood_request.hospital_name
        ).first()

    if hospital is None:
        return jsonify({
            "status": "unavailable",
            "message": "Hospital inventory not found",
            "blood_group": blood_request.blood_group,
            "available_units": 0,
            "required_units": blood_request.units_needed or 1
        }), 200

    # -------------------------------------------------
    # Get inventory for requested blood group
    # -------------------------------------------------

    inventory_rows = get_inventory(hospital.hospital_id)

    requested_group = (
        blood_request.blood_group or ""
    ).strip().upper()

    inventory_item = None

    for item in inventory_rows:

        item_group = (
            getattr(item, "blood_group", "") or ""
        ).strip().upper()

        if item_group == requested_group:
            inventory_item = item
            break

    required_units = blood_request.units_needed or 1

    if inventory_item is None:

        return jsonify({
            "status": "unavailable",
            "message": "No blood stock available for this blood group",
            "blood_group": requested_group,
            "available_units": 0,
            "required_units": required_units,
            "hospital_id": hospital.hospital_id,
            "hospital_name": hospital.hospital_name
        }), 200

    available_units = getattr(
        inventory_item,
        "available_units",
        0
    ) or 0

    available_units = int(available_units)

    sufficient = available_units >= required_units

    return jsonify({
        "status": "available" if sufficient else "insufficient",
        "message": (
            "Blood available in hospital inventory"
            if sufficient
            else "Insufficient blood stock"
        ),
        "blood_group": requested_group,
        "available_units": available_units,
        "required_units": required_units,
        "sufficient": sufficient,
        "hospital_id": hospital.hospital_id,
        "hospital_name": hospital.hospital_name
    }), 200