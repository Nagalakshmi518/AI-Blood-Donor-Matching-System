from app import db

from app.models.notification import Notification


def create_notification(data):

    notification_type = data.get(
        "notification_type",
        data.get("type")
    )

    notification = Notification(

        user_id=data.get(
            "user_id"
        ),

        title=data.get(
            "title",
            "Blood Request Notification"
        ),

        message=data.get(
            "message"
        ),

        notification_type=notification_type,

        related_request_id=data.get(
            "related_request_id"
        ),

        is_read=data.get(
            "is_read",
            False
        )

    )

    db.session.add(
        notification
    )

    db.session.commit()

    return notification