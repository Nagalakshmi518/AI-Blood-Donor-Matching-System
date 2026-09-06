from app import db


class Donation(db.Model):
    __tablename__ = "donations"

    donation_id = db.Column(
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

    request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_requests.request_id"),
        nullable=False
    )

    donation_date = db.Column(
        db.Date,
        nullable=False
    )

    units_donated = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
    donation_status = db.Column(
    db.Enum(
        "Pending",
        "Completed"
    ),
    default="Pending",
    nullable=False
)

    def to_dict(self):
        return {
            "donation_id": self.donation_id,
            "donor_id": self.donor_id,
            "patient_id": self.patient_id,
            "request_id": self.request_id,
            "donation_date": str(self.donation_date),
            "units_donated": self.units_donated,
            "donation_status": self.donation_status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.created_at else None
        }