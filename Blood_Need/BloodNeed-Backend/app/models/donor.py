from app import db
from app.models.user import User


class Donor(db.Model):
    __tablename__ = "donors"

    donor_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False
    )

    blood_group = db.Column(db.String(5), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Enum("Male", "Female", "Other"), nullable=False)
    weight = db.Column(db.Float, nullable=False, default=50)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.Text)

    last_donation_date = db.Column(db.Date)
    next_eligible_date = db.Column(db.Date)

    last_response_time = db.Column(db.DateTime)

    successful_donations = db.Column(db.Integer, default=0)
    rejected_requests = db.Column(db.Integer, default=0)
    accepted_requests = db.Column(db.Integer, default=0)

    total_donations = db.Column(db.Integer, default=0)

    # Donor Availability
    availability = db.Column(db.Boolean, default=True)
    reliability_score = db.Column(db.Float, default=0.0)
    reward_points = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50), default="New Donor")

    # -------------------------
    # Relationships
    # -------------------------

    matches = db.relationship(
        "DonorMatch", back_populates="donor", lazy=True, cascade="all, delete-orphan"
    )

    donations = db.relationship(
        "Donation", backref="donor", lazy=True, cascade="all, delete-orphan"
    )

    feedbacks = db.relationship(
        "Feedback", backref="donor", lazy=True, cascade="all, delete-orphan"
    )

    rewards = db.relationship(
        "RewardPoint", backref="donor", lazy=True, cascade="all, delete-orphan"
    )

    badges = db.relationship(
        "Badge", backref="donor", lazy=True, cascade="all, delete-orphan"
    )

    response_history = db.relationship(
        "ResponseHistory", backref="donor", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        user = User.query.get(self.user_id)

        total_points = sum(getattr(reward, 'points', 0) for reward in self.rewards or [])

        badge_names = [badge.badge_name for badge in (self.badges or []) if getattr(badge, 'is_active', False)]

        return {
            "donor_id": self.donor_id,
            "user_id": self.user_id,
            "full_name": (user.full_name if user and getattr(user, 'full_name', None) else "Unknown Donor"),
            "phone": user.phone if user else None,
            "email": user.email if user else None,
            "blood_group": self.blood_group,
            "age": self.age,
            "gender": self.gender,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "last_donation_date": str(self.last_donation_date) if self.last_donation_date else None,
            "weight": self.weight,
            "next_eligible_date": str(self.next_eligible_date) if self.next_eligible_date else None,
            "successful_donations": self.successful_donations,
            "accepted_requests": self.accepted_requests,
            "rejected_requests": self.rejected_requests,
            "total_donations": self.total_donations,
            "availability": self.availability,
            "reliability_score": self.reliability_score,
            "reward_points": total_points,
            "badge": self.badge,
            "badges": badge_names,
        }

    def to_public_dict(self, distance_km=None, ranking_score=None, donor_response="Pending", response_probability=None, include_private=False):
        user = User.query.get(self.user_id)
        public_data = {
            "donor_id": self.donor_id,
            "full_name": user.full_name if user else "Unknown Donor",
            "blood_group": self.blood_group,
            "availability": self.availability,
            "distance_km": round(distance_km, 2) if distance_km is not None else None,
            "ranking_score": round(ranking_score, 2) if ranking_score is not None else None,
            "response_probability": round(response_probability, 2) if response_probability is not None else None,
            "donor_response": donor_response,
            "match_status": donor_response,
        }

        if include_private:
            public_data.update({
                "phone": user.phone if user else None,
                "email": user.email if user else None,
                "latitude": self.latitude,
                "longitude": self.longitude,
            })

        return public_data