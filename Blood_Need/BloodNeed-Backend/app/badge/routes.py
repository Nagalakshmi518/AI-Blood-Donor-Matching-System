from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.badge.services import (
    create_badge,
    get_all_badges,
    get_badge,
    get_badges_by_donor,
    update_badge,
    delete_badge
)

from app.schemas.badge_schema import validate_badge

badge_bp = Blueprint(
    "badge",
    __name__,
    url_prefix="/api/badges"
)


@badge_bp.route("/", methods=["GET"])
@jwt_required()
def badges():

    badges = get_all_badges()

    return jsonify([
        badge.to_dict()
        for badge in badges
    ])


@badge_bp.route("/<int:badge_id>", methods=["GET"])
@jwt_required()
def badge(badge_id):

    badge = get_badge(badge_id)

    if badge is None:
        return jsonify({
            "message": "Badge not found"
        }), 404

    return jsonify(
        badge.to_dict()
    )


@badge_bp.route("/", methods=["POST"])
@jwt_required()
def add_badge():

    data = request.get_json()

    valid, message = validate_badge(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    badge = create_badge(data)

    return jsonify(
        badge.to_dict()
    ), 201


@badge_bp.route("/<int:badge_id>", methods=["PUT"])
@jwt_required()
def edit_badge(badge_id):

    badge = get_badge(badge_id)

    if badge is None:
        return jsonify({
            "message": "Badge not found"
        }), 404

    badge = update_badge(
        badge,
        request.get_json()
    )

    return jsonify(
        badge.to_dict()
    )


@badge_bp.route("/<int:badge_id>", methods=["DELETE"])
@jwt_required()
def remove_badge(badge_id):

    badge = get_badge(badge_id)

    if badge is None:
        return jsonify({
            "message": "Badge not found"
        }), 404

    delete_badge(badge)

    return jsonify({
        "message": "Badge deleted successfully"
    })


@badge_bp.route("/donor/<int:donor_id>", methods=["GET"])
@jwt_required()
def donor_badges(donor_id):

    badges = get_badges_by_donor(
        donor_id
    )

    return jsonify([
        badge.to_dict()
        for badge in badges
    ])