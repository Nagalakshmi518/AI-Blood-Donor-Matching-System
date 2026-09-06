from app import db


class Badge(db.Model):

    __tablename__ = "badges"


    badge_id = db.Column(

        db.Integer,

        primary_key=True

    )


    donor_id = db.Column(

        db.Integer,

        db.ForeignKey(

            "donors.donor_id"

        ),

        nullable=False

    )


    badge_name = db.Column(

        db.String(100),

        nullable=False

    )


    badge_description = db.Column(

        db.String(255)

    )


    badge_icon = db.Column(

        db.String(255)

    )


    awarded_at = db.Column(

        db.DateTime,

        server_default=db.func.now()

    )


    is_active = db.Column(

        db.Boolean,

        default=True,

        nullable=False

    )


    def to_dict(self):

        return {

            "badge_id":
                self.badge_id,

            "donor_id":
                self.donor_id,

            "badge_name":
                self.badge_name,

            "badge_description":
                self.badge_description,

            "badge_icon":
                self.badge_icon,

            "awarded_at":

                self.awarded_at.isoformat()

                if self.awarded_at

                else None,

            "is_active":
                self.is_active

        }