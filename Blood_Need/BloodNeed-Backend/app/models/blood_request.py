from app import db


class BloodRequest(db.Model):
    __tablename__ = "blood_requests"

    request_id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.patient_id"),
        nullable=False
    )
    hospital_id = db.Column(
    db.Integer,
    db.ForeignKey("hospitals.hospital_id"),
    nullable=True
)
    blood_group = db.Column(
        db.String(5),
        nullable=False
    )

    units_needed = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    emergency_level = db.Column(
        db.Enum("LOW", "MEDIUM", "HIGH", "CRITICAL"),
        nullable=False
    )

    hospital_name = db.Column(
        db.String(200),
        nullable=False
    )

    hospital_latitude = db.Column(db.Float)

    hospital_longitude = db.Column(db.Float)

    notes = db.Column(db.Text)

    status = db.Column(
        db.Enum(
            "Pending",
            "Matched",
            "Accepted",
            "Completed",
            "Cancelled"
        ),
        default="Pending"
    )
    fulfillment_source = db.Column(
    db.String(50),
    nullable=True
)
    request_time = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # -------------------------
    # Relationships
    # -------------------------
    hospital = db.relationship(
    "Hospital",
    backref="blood_requests",
    lazy=True
)
    matches = db.relationship(
        "DonorMatch",
        back_populates="blood_request",
        lazy=True,
        cascade="all, delete-orphan"
    )

    donations = db.relationship(
        "Donation",
        backref="blood_request",
        lazy=True,
        cascade="all, delete-orphan"
    )

    response_history = db.relationship(
        "ResponseHistory",
        backref="blood_request",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self):
     return {
        "request_id": self.request_id,
        "patient_id": self.patient_id,
        "hospital_id": self.hospital_id,
        "blood_group": self.blood_group,
        "units_needed": self.units_needed,
        "emergency_level": self.emergency_level,
        "hospital_name": self.hospital_name,
        "hospital_latitude": self.hospital_latitude,
        "hospital_longitude": self.hospital_longitude,
        "notes": self.notes,
        "status": self.status,
        "fulfillment_source": self.fulfillment_source,

        "request_time": (
            self.request_time.strftime("%Y-%m-%d %H:%M:%S")
            if self.request_time
            else None
        ),

    }