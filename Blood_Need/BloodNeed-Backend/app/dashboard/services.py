from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation


def dashboard_summary():

    return {

        "total_users": User.query.count(),

        "total_donors": Donor.query.count(),

        "total_patients": Patient.query.count(),

        "available_donors":
        Donor.query.filter_by(availability=True).count(),

        "total_requests":
        BloodRequest.query.count(),

        "pending_requests":
        BloodRequest.query.filter_by(
            status="Pending"
        ).count(),

        "accepted_requests":
        BloodRequest.query.filter_by(
            status="Accepted"
        ).count(),

        "completed_requests":
        BloodRequest.query.filter_by(
            status="Completed"
        ).count(),

        "cancelled_requests":
        BloodRequest.query.filter_by(
            status="Cancelled"
        ).count(),

        "total_donations":
        Donation.query.count()
    }