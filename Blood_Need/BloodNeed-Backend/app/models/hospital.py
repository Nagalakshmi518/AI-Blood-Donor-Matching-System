from app import db


class Hospital(db.Model):
    __tablename__ = "hospitals"

    hospital_id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
    db.Integer,
    db.ForeignKey("users.user_id"),
    unique=True,
    nullable=True
)

    user = db.relationship(
    "User",
    backref=db.backref(
        "hospital_profile",
        uselist=False
    )
)
    hospital_name = db.Column(
        db.String(200),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    phone = db.Column(
        db.String(15)
    )

    email = db.Column(
        db.String(100)
    )

    city = db.Column(
        db.String(100)
    )

    state = db.Column(
        db.String(100)
    )

    pincode = db.Column(
        db.String(10)
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "hospital_id": self.hospital_id,
            "user_id": self.user_id,
            "hospital_name": self.hospital_name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "phone": self.phone,
            "email": self.email,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "is_active": self.is_active,
            "created_at": self.created_at
        }