from app import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id = db.Column(
        db.Integer,
        primary_key=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("donors.donor_id"),
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.patient_id"),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comments = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "feedback_id": self.feedback_id,
            "donor_id": self.donor_id,
            "patient_id": self.patient_id,
            "rating": self.rating,
            "comments": self.comments,
            "created_at": self.created_at
        }