from app import db


class HospitalInventory(db.Model):
    __tablename__ = "hospital_inventories"

    inventory_id = db.Column(db.Integer, primary_key=True)

    hospital_id = db.Column(
        db.Integer, db.ForeignKey("hospitals.hospital_id"), nullable=False
    )

    blood_group = db.Column(db.String(5), nullable=False)

    available_units = db.Column(db.Integer, nullable=False, default=0)

    last_updated = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    hospital = db.relationship("Hospital", backref="inventories")

    __table_args__ = (
        db.UniqueConstraint("hospital_id", "blood_group", name="hospital_blood_unique"),
    )

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "hospital_id": self.hospital_id,
            "blood_group": self.blood_group,
            "available_units": self.available_units,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None,
        }