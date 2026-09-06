from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.reward.services import (
    get_rewards,
    get_total_points,
    get_badges
)

reward_bp = Blueprint(
    "reward",
    __name__,
    url_prefix="/api/rewards"
)


@reward_bp.route("/<int:donor_id>", methods=["GET"])
@jwt_required()
def rewards(donor_id):

    rewards = get_rewards(donor_id)

    return jsonify([
        reward.to_dict()
        for reward in rewards
    ])


@reward_bp.route("/<int:donor_id>/total", methods=["GET"])
@jwt_required()
def total_points(donor_id):

    return jsonify({
        "total_points": get_total_points(donor_id)
    })


@reward_bp.route("/<int:donor_id>/badges", methods=["GET"])
@jwt_required()
def badges(donor_id):

    badges = get_badges(donor_id)

    return jsonify([
        badge.to_dict()
        for badge in badges
    ])