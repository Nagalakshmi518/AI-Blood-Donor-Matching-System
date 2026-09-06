from app import db

class PasswordReset(db.Model):

    __tablename__="password_reset"

    reset_id=db.Column(
        db.Integer,
        primary_key=True
    )

    email=db.Column(
        db.String(100),
        nullable=False
    )

    otp=db.Column(
        db.String(6),
        nullable=False
    )

    verified=db.Column(
        db.Boolean,
        default=False
    )