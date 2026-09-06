from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.models.blood_request import BloodRequest
from app.models.donor_match import DonorMatch


matching_bp = Blueprint(
    "matching",
    __name__,
    url_prefix="/api/matching"
)


@matching_bp.route("/<int:request_id>", methods=["GET"])
@jwt_required()
def get_matches(request_id):

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:
        return jsonify({
            "message": "Blood request not found"
        }), 404

    matches = DonorMatch.query.filter_by(
        request_id=request_id
    ).order_by(
        DonorMatch.ranking_score.desc()
    ).all()

    if not matches:

        return jsonify({
            "message": "No matching donors found"
        }), 404

    return jsonify({
    "request_id": blood_request.request_id,
    "blood_group": blood_request.blood_group,

    "hospital_name": blood_request.hospital_name,
    "hospital_latitude": blood_request.hospital_latitude,
    "hospital_longitude": blood_request.hospital_longitude,
    "emergency_level": blood_request.emergency_level,
    "status": blood_request.status,

    "total_matches": len(matches),

    "matched_donors": [
        {
            "donor": match.donor.to_public_dict(
                distance_km=match.distance_km,
                ranking_score=match.ranking_score,
                donor_response=match.donor_response
            ),
            "distance_km": match.distance_km,
            "donor_response": match.donor_response,
            "response_deadline": match.response_deadline,
            "match_id": match.match_id
        }
        for match in matches
    ]
}), 200