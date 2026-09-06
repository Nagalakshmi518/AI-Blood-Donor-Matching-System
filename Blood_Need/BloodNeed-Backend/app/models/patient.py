from app import db
from app.models.user import User


class Patient(db.Model):

    __tablename__ = "patients"

    patient_id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        unique=True,
        nullable=False
    )

    blood_group = db.Column(
        db.String(5),
        nullable=True
    )

    age = db.Column(
        db.Integer,
        nullable=True
    )

    gender = db.Column(
        db.Enum(
            "Male",
            "Female",
            "Other"
        ),
        nullable=True
    )

    hospital_name = db.Column(
        db.String(200),
        nullable=True
    )

    latitude = db.Column(db.Float,nullable=True)

    longitude = db.Column(db.Float,nullable=True)

    # =========================
    # Relationships
    # =========================

    blood_requests = db.relationship(
        "BloodRequest",
        backref="patient",
        lazy=True,
        cascade="all, delete"
    )

    donations = db.relationship(
        "Donation",
        backref="patient",
        lazy=True,
        cascade="all, delete"
    )

    feedbacks = db.relationship(
        "Feedback",
        backref="patient",
        lazy=True,
        cascade="all, delete"
    )

    # =========================
    # Convert to Dictionary
    # =========================

    def to_dict(self):

        user = User.query.get(self.user_id)

        return {

            "patient_id": self.patient_id,

            "user_id": self.user_id,

            "full_name":
                user.full_name
                if user else None,

            "phone":
                user.phone
                if user else None,

            "email":
                user.email
                if user else None,

            "blood_group": self.blood_group,

            "age": self.age,

            "gender": self.gender,

            "hospital_name": self.hospital_name,

            "latitude": self.latitude,

            "longitude": self.longitude

        }
    