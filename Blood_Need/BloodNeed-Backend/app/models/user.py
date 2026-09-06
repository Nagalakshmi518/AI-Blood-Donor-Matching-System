from app import db


class User(db.Model):

    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.Enum(
            "ADMIN",
            "DONOR",
            "PATIENT",
            "HOSPITAL"
        ),
        nullable=False,
        default="PATIENT"
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    # Email verification flag
    is_email_verified = db.Column(
        db.Boolean,
        default=False
    )

    # =========================
    # Convert to Dictionary
    # =========================

    def to_dict(self):

        return {

            "user_id": self.user_id,

            "full_name": self.full_name,

            "email": self.email,

            "phone": self.phone,

            "role": self.role,

            "active": self.active

        }
    