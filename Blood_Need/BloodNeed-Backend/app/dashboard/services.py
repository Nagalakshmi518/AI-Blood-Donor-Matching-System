from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation


def dashboard_summary(user_id=None):
    donor_counts = dict(
        db.session.query(
            Donor.availability,
            func.count(Donor.donor_id)
        )
        .group_by(Donor.availability)
        .all()
    )

    request_counts = dict(
        db.session.query(
            BloodRequest.status,
            func.count(BloodRequest.request_id)
        )
        .group_by(BloodRequest.status)
        .all()
    )

    return {
        "total_users": User.query.count(),
        "total_donors": sum(donor_counts.values()),
        "total_patients": Patient.query.count(),
        "available_donors": donor_counts.get(True, 0),
        "total_requests": sum(request_counts.values()),
        "pending_requests": request_counts.get("Pending", 0),
        "accepted_requests": request_counts.get("Accepted", 0),
        "completed_requests": request_counts.get("Completed", 0),
        "cancelled_requests": request_counts.get("Cancelled", 0),
        "total_donations": Donation.query.count()
    }