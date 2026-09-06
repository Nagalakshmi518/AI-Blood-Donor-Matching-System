from app import db


class ResponseHistory(db.Model):
    __tablename__ = "response_history"

    history_id = db.Column(
        db.Integer,
        primary_key=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("donors.donor_id"),
        nullable=False
    )

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.request_id"),
        nullable=False
    )

    response_status = db.Column(
        db.Enum(
            "Accepted",
            "Rejected",
            "Missed"
        ),
        nullable=False
    )

    response_time_seconds = db.Column(
        db.Integer,
        nullable=False
    )

    ai_score = db.Column(
        db.Float,
        default=0.0
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "history_id": self.history_id,
            "donor_id": self.donor_id,
            "request_id": self.request_id,
            "response_status": self.response_status,
            "response_time_seconds": self.response_time_seconds,
            "ai_score": self.ai_score,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None
        }