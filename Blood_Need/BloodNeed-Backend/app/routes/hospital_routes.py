from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.hospital import Hospital


hospital_bp = Blueprint(
    "hospital",
    __name__,
    url_prefix="/api/hospitals"
)


# ==========================================
# GET LOGGED-IN HOSPITAL PROFILE
# ==========================================

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