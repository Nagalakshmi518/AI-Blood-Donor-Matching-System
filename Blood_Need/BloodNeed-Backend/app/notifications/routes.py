from flask import Blueprint, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from app.models.notification import Notification

from app import db


notification_bp = Blueprint(

    "notification",

    __name__,

    url_prefix="/api/notifications"

)


# ==========================================
# GET MY NOTIFICATIONS
# ==========================================

@notification_bp.route(
    "/",
    methods=["GET"]
)
@jwt_required()
def get_my_notifications():

    user_id = get_jwt_identity()

    notifications = (
        Notification.query
        .filter_by(
            user_id=user_id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )

    return jsonify([

        notification.to_dict()

        for notification in notifications

    ])


# ==========================================
# MARK NOTIFICATION AS READ
# ==========================================

@notification_bp.route(
    "/<int:notification_id>/read",
    methods=["PATCH"]
)
@jwt_required()
def mark_as_read(notification_id):

    user_id = get_jwt_identity()

    notification = (
        Notification.query
        .filter_by(

            notification_id=notification_id,

            user_id=user_id

        )
        .first()
    )

    if notification is None:

        return jsonify({

            "message":
                "Notification not found"

        }), 404

    notification.is_read = True

    db.session.commit()

    return jsonify({

        "message":
            "Notification marked as read"

    }), 200