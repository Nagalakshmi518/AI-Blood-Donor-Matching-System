from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.response.services import (
    accept_request,
    reject_request
)

response_bp = Blueprint(
    "response",
    __name__,
    url_prefix="/api/response"
)


# ==========================================
# ACCEPT BLOOD REQUEST
# ==========================================

@response_bp.route("/<int:match_id>/accept", methods=["PATCH"])
@jwt_required()
def accept(match_id):

    user_id = get_jwt_identity()

    match = accept_request(match_id, user_id)

    if match is None:
        return jsonify({
            "message": "Match not found, expired or already responded"
        }), 404

    return jsonify({
        "message": "Blood request accepted successfully",
        "match_id": match.match_id,
        "status": match.donor_response
    }), 200


# ==========================================
# REJECT BLOOD REQUEST
# ==========================================

@response_bp.route("/<int:match_id>/reject", methods=["PATCH"])
@jwt_required()
def reject(match_id):

    user_id = get_jwt_identity()

    match = reject_request(match_id, user_id)

    if match is None:
        return jsonify({
            "message": "Match not found, expired or already responded"
        }), 404

    return jsonify({
        "message": "Blood request rejected successfully",
        "match_id": match.match_id,
        "status": match.donor_response
    }), 200