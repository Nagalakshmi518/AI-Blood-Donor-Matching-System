from app import db


class RewardPoint(db.Model):

    __tablename__ = "reward_points"

    reward_id = db.Column(
        db.Integer,
        primary_key=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("donors.donor_id"),
        nullable=False
    )

    points = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    reason = db.Column(
        db.String(255),
        nullable=False
    )

    earned_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):

        return {

            "reward_id":
                self.reward_id,

            "donor_id":
                self.donor_id,

            "points":
                self.points,

            "reason":
                self.reason,

            "earned_at":

                self.earned_at.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if self.earned_at
                else None

        }