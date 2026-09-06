from flask import Blueprint, request, jsonify

from flask_jwt_extended import jwt_required

from app.donation.services import (

    create_donation,

    get_all_donations,

    get_donation,

    delete_donation,
    mark_donation_completed


)

from app.schemas.donation_schema import validate_donation


donation_bp = Blueprint(

    "donation",

    __name__,

    url_prefix="/api/donations"

)


# =====================================================
# GET ALL DONATIONS
# =====================================================

@donation_bp.route("/", methods=["GET"])
@jwt_required()
def donations():

    donations = get_all_donations()


    return jsonify([

        donation.to_dict()

        for donation in donations

    ])


# =====================================================
# GET DONATION BY ID
# =====================================================

@donation_bp.route(

    "/<int:donation_id>",

    methods=["GET"]

)

@jwt_required()
def donation(donation_id):

    donation = get_donation(

        donation_id

    )


    if donation is None:

        return jsonify({

            "message": "Donation not found"

        }), 404


    return jsonify(

        donation.to_dict()

    )


# =====================================================
# CREATE DONATION
# =====================================================

@donation_bp.route(

    "/",

    methods=["POST"]

)

@jwt_required()
def add_donation():

    data = request.get_json()


    if not data:

        return jsonify({

            "message": "Request body is required"

        }), 400


    valid, message = validate_donation(

        data

    )


    if not valid:

        return jsonify({

            "message": message

        }), 400


    donation, error = create_donation(

        data

    )


    if donation is None:

        return jsonify({

            "message": error

        }), 400


    return jsonify(

        donation.to_dict()

    ), 201


# =====================================================
# DELETE DONATION
# =====================================================

@donation_bp.route(

    "/<int:donation_id>",

    methods=["DELETE"]

)

@jwt_required()
def remove_donation(donation_id):

    donation = get_donation(

        donation_id

    )


    if donation is None:

        return jsonify({

            "message": "Donation not found"

        }), 404


    delete_donation(

        donation

    )


    return jsonify({

        "message": "Donation deleted successfully"

    })
# =====================================================
# COMPLETE DONATION
# =====================================================
@donation_bp.route("/<int:donation_id>/complete", methods=["PATCH"])
@jwt_required()
def complete_donation(donation_id):

    donation = mark_donation_completed(donation_id)

    if donation is None:
        return jsonify({
            "message": "Donation not found"
        }), 404

    return jsonify({
        "message": "Donation completed successfully",
        "donation": donation.to_dict()
    }), 200