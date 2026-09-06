from app.models.donor import Donor
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.donor_match import DonorMatch
from app import db
from sqlalchemy import func
# ====================================================
# BLOOD GROUP STATISTICS
# ====================================================

def blood_group_statistics():

    result = db.session.query(
        BloodRequest.blood_group,
        func.count(BloodRequest.request_id)
    ).group_by(
        BloodRequest.blood_group
    ).all()

    return [
        {
            "blood_group": blood_group,
            "count": count
        }
        for blood_group, count in result
    ]
# ====================================================
# DONOR AVAILABILITY
# ====================================================

def donor_availability_statistics():

    available = Donor.query.filter_by(
        availability=True
    ).count()

    unavailable = Donor.query.filter_by(
        availability=False
    ).count()

    return {
        "available": available,
        "unavailable": unavailable
    }
# ====================================================
# EMERGENCY LEVEL STATISTICS
# ====================================================

def emergency_statistics():

    result = db.session.query(
        BloodRequest.emergency_level,
        func.count(BloodRequest.request_id)
    ).group_by(
        BloodRequest.emergency_level
    ).all()

    return [
        {
            "emergency_level": level,
            "count": count
        }
        for level, count in result
    ]
# ====================================================
# MATCHING STATISTICS
# ====================================================

def matching_statistics():

    total = DonorMatch.query.count()

    accepted = DonorMatch.query.filter_by(
        donor_response="Accepted"
    ).count()

    rejected = DonorMatch.query.filter_by(
        donor_response="Rejected"
    ).count()

    pending = DonorMatch.query.filter_by(
        donor_response="Pending"
    ).count()

    return {
        "total_matches": total,
        "accepted": accepted,
        "rejected": rejected,
        "pending": pending
    }
# ====================================================
# DONATION STATISTICS
# ====================================================

def donation_statistics():

    return {
        "total_donations":
            Donation.query.count()
    }