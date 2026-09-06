from datetime import datetime, timedelta
from app import db


class EmailVerification(db.Model):
    __tablename__ = "email_verifications"

    verification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    email = db.Column(db.String(150), nullable=False, index=True)

    # store a hash of the OTP, not the plaintext OTP
    otp_hash = db.Column(db.String(255), nullable=False)

    # purpose: 'verify' or 'reset'
    purpose = db.Column(db.Enum("verify", "reset"), nullable=False, default="verify")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)

    def mark_used(self):
        self.used = True
        self.used_at = datetime.utcnow()

    @classmethod
    def make_record(cls, email, otp_hash, purpose="verify", ttl_minutes=10, user_id=None):
        now = datetime.utcnow()
        return cls(
            user_id=user_id,
            email=email,
            otp_hash=otp_hash,
            purpose=purpose,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
            used=False,
        )

    def to_dict(self):
        return {
            "verification_id": self.verification_id,
            "user_id": self.user_id,
            "email": self.email,
            "purpose": self.purpose,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "expires_at": self.expires_at.strftime("%Y-%m-%d %H:%M:%S") if self.expires_at else None,
            "used": self.used,
            "used_at": self.used_at.strftime("%Y-%m-%d %H:%M:%S") if self.used_at else None,
        }