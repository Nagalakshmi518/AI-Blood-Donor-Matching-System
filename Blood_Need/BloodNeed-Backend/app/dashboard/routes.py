from flask import Blueprint, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from app.dashboard.services import dashboard_summary


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard"
)


@dashboard_bp.route(
    "/summary",
    methods=["GET"]
)
@jwt_required()
def summary():

    user_id = get_jwt_identity()

    dashboard_data = dashboard_summary(
        user_id
    )

    return jsonify(
        dashboard_data
    ), 200