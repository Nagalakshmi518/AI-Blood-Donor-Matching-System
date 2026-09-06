from app import db


class DonorMatch(db.Model):

    __tablename__ = "donor_matches"


    match_id = db.Column(
        db.Integer,
        primary_key=True
    )


    request_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "blood_requests.request_id"
        ),
        nullable=False
    )


    donor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "donors.donor_id"
        ),
        nullable=False
    )


    distance_km = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )


    response_probability = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )


    ranking_score = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )


    donor_response = db.Column(

        db.Enum(

            "Pending",

            "Accepted",

            "Rejected",

            "Missed"

        ),

        nullable=False,

        default="Pending"

    )


    matched_at = db.Column(

        db.DateTime,

        server_default=db.func.now()

    )


    response_deadline = db.Column(

        db.DateTime,

        nullable=True

    )


    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    donor = db.relationship(

        "Donor",

        back_populates="matches"

    )


    blood_request = db.relationship(

        "BloodRequest",

        back_populates="matches"

    )


    # ==========================================
    # TO DICTIONARY
    # ==========================================

    def to_dict(self):

        return {

            "match_id":
                self.match_id,

            "request_id":
                self.request_id,

            "donor_id":
                self.donor_id,

            "distance_km":
                self.distance_km,

            "response_probability":
                self.response_probability,

            "ranking_score":
                self.ranking_score,

            "donor_response":
                self.donor_response,

            "matched_at":

                self.matched_at.strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

                if self.matched_at

                else None,

            "response_deadline":

                self.response_deadline.strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

                if self.response_deadline

                else None

        }