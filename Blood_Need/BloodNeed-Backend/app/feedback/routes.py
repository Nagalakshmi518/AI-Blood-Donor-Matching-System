from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.feedback.services import (
    create_feedback,
    get_all_feedback,
    get_feedback,
    get_feedback_by_donor,
    get_feedback_by_patient,
    update_feedback,
    delete_feedback,
    calculate_average_rating
)

from app.schemas.feedback_schema import validate_feedback

feedback_bp = Blueprint(
    "feedback",
    __name__,
    url_prefix="/api/feedback"
)


# ---------------------------------
# Get All Feedback
# ---------------------------------
@feedback_bp.route("/", methods=["GET"])
@jwt_required()
def feedbacks():

    feedbacks = get_all_feedback()

    return jsonify([
        feedback.to_dict()
        for feedback in feedbacks
    ])


# ---------------------------------
# Get Feedback By ID
# ---------------------------------
@feedback_bp.route("/<int:feedback_id>", methods=["GET"])
@jwt_required()
def feedback(feedback_id):

    feedback = get_feedback(feedback_id)

    if feedback is None:
        return jsonify({
            "message": "Feedback not found"
        }), 404

    return jsonify(
        feedback.to_dict()
    )


# ---------------------------------
# Add Feedback
# ---------------------------------
@feedback_bp.route("/", methods=["POST"])
@jwt_required()
def add_feedback():

    data = request.get_json()

    valid, message = validate_feedback(data)

    if not valid:
        return jsonify({
            "message": message
        }), 400

    feedback = create_feedback(data)

    return jsonify(
        feedback.to_dict()
    ), 201


# ---------------------------------
# Update Feedback
# ---------------------------------
@feedback_bp.route("/<int:feedback_id>", methods=["PUT"])
@jwt_required()
def edit_feedback(feedback_id):

    feedback = get_feedback(feedback_id)

    if feedback is None:
        return jsonify({
            "message": "Feedback not found"
        }), 404

    feedback = update_feedback(
        feedback,
        request.get_json()
    )

    return jsonify(
        feedback.to_dict()
    )


# ---------------------------------
# Delete Feedback
# ---------------------------------
@feedback_bp.route("/<int:feedback_id>", methods=["DELETE"])
@jwt_required()
def remove_feedback(feedback_id):

    feedback = get_feedback(feedback_id)

    if feedback is None:
        return jsonify({
            "message": "Feedback not found"
        }), 404

    delete_feedback(feedback)

    return jsonify({
        "message": "Feedback deleted successfully"
    })


# ---------------------------------
# Get Feedback By Donor
# ---------------------------------
@feedback_bp.route("/donor/<int:donor_id>", methods=["GET"])
@jwt_required()
def donor_feedback(donor_id):

    feedbacks = get_feedback_by_donor(
        donor_id
    )

    return jsonify([
        feedback.to_dict()
        for feedback in feedbacks
    ])


# ---------------------------------
# Get Feedback By Patient
# ---------------------------------
@feedback_bp.route("/patient/<int:patient_id>", methods=["GET"])
@jwt_required()
def patient_feedback(patient_id):

    feedbacks = get_feedback_by_patient(
        patient_id
    )

    return jsonify([
        feedback.to_dict()
        for feedback in feedbacks
    ])


# ---------------------------------
# Average Rating
# ---------------------------------
@feedback_bp.route(
    "/donor/<int:donor_id>/average-rating",
    methods=["GET"]
)
@jwt_required()
def average_rating(donor_id):

    rating = calculate_average_rating(
        donor_id
    )

    return jsonify({
        "donor_id": donor_id,
        "average_rating": rating
    })