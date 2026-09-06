from app import db


class Notification(db.Model):

    __tablename__ = "notifications"

    notification_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=True
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False
    )

    related_request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.request_id"),
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):

        return {

            "notification_id":
                self.notification_id,

            "user_id":
                self.user_id,

            "title":
                self.title,

            "message":
                self.message,

            # Frontend uses notification.type
            "type":
                self.notification_type,

            "notification_type":
                self.notification_type,

            "related_request_id":
                self.related_request_id,

            "is_read":
                self.is_read,

            "created_at":

                self.created_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if self.created_at
                else None

        }