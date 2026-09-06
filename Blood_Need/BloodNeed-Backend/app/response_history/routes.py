from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.response_history.services import (
    create_history,
    get_all_history,
    get_history,
    get_history_by_donor,
    get_history_by_request,
    update_history,
    delete_history
)

from app.schemas.response_history_schema import validate_history

response_history_bp = Blueprint(
    "response_history",
    __name__,
    url_prefix="/api/response-history"
)


@response_history_bp.route("/", methods=["GET"])
@jwt_required()
def histories():

    history = get_all_history()

    return jsonify([
        h.to_dict()
        for h in history
    ])


@response_history_bp.route("/<int:history_id>", methods=["GET"])
@jwt_required()
def history(history_id):

    history = get_history(history_id)

    if history is None:
        return jsonify({
            "message": "History not found"
        }), 404

    return jsonify(history.to_dict())


@response_history_bp.route("/", methods=["POST"])
@jwt_required()
def add_history():

    data = request.get_json()

    valid, message = validate_history(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    history = create_history(data)

    return jsonify(history.to_dict()), 201


@response_history_bp.route("/<int:history_id>", methods=["PUT"])
@jwt_required()
def edit_history(history_id):

    history = get_history(history_id)

    if history is None:
        return jsonify({
            "message": "History not found"
        }), 404

    history = update_history(
        history,
        request.get_json()
    )

    return jsonify(history.to_dict())


@response_history_bp.route("/<int:history_id>", methods=["DELETE"])
@jwt_required()
def remove_history(history_id):

    history = get_history(history_id)

    if history is None:
        return jsonify({
            "message": "History not found"
        }), 404

    delete_history(history)

    return jsonify({
        "message": "History deleted successfully"
    })


@response_history_bp.route("/donor/<int:donor_id>", methods=["GET"])
@jwt_required()
def donor_history(donor_id):

    history = get_history_by_donor(donor_id)

    return jsonify([
        h.to_dict()
        for h in history
    ])


@response_history_bp.route("/request/<int:request_id>", methods=["GET"])
@jwt_required()
def request_history(request_id):

    history = get_history_by_request(request_id)

    return jsonify([
        h.to_dict()
        for h in history
    ])