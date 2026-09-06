from app import db

from app.models.user import User
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.donor_match import DonorMatch


# ====================================================
# ADMIN DASHBOARD SUMMARY
# ====================================================

def get_admin_summary():

    return {

        "total_users": User.query.count(),

        "total_donors": Donor.query.count(),

        "total_patients": Patient.query.count(),

        "available_donors": Donor.query.filter_by(
            availability=True
        ).count(),

        "total_requests": BloodRequest.query.count(),

        "pending_requests": BloodRequest.query.filter_by(
            status="Pending"
        ).count(),

        "matched_requests": BloodRequest.query.filter_by(
            status="Matched"
        ).count(),

        "accepted_requests": BloodRequest.query.filter_by(
            status="Accepted"
        ).count(),

        "completed_requests": BloodRequest.query.filter_by(
            status="Completed"
        ).count(),

        "cancelled_requests": BloodRequest.query.filter_by(
            status="Cancelled"
        ).count(),

        "total_donations": Donation.query.count(),

        "total_matches": DonorMatch.query.count()

    }


# ====================================================
# GET ALL USERS
# ====================================================

def get_all_users():

    return User.query.order_by(
        User.user_id.desc()
    ).all()


# ====================================================
# GET ALL DONORS
# ====================================================

def get_all_donors():

    return Donor.query.order_by(
        Donor.donor_id.desc()
    ).all()


# ====================================================
# GET ALL PATIENTS
# ====================================================

def get_all_patients():

    return Patient.query.order_by(
        Patient.patient_id.desc()
    ).all()


# ====================================================
# GET ALL BLOOD REQUESTS
# ====================================================

def get_all_blood_requests():

    return BloodRequest.query.order_by(
        BloodRequest.request_id.desc()
    ).all()


# ====================================================
# GET ALL DONATIONS
# ====================================================

def get_all_donations():

    return Donation.query.order_by(
        Donation.donation_id.desc()
    ).all()


# ====================================================
# GET ALL MATCHES
# ====================================================

def get_all_matches():

    return DonorMatch.query.order_by(
        DonorMatch.match_id.desc()
    ).all()


# ====================================================
# DELETE BLOOD REQUEST
# ====================================================

def delete_blood_request(request_id):

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:
        return False

    db.session.delete(blood_request)
    db.session.commit()

    return True


# ====================================================
# DELETE DONOR
# ====================================================

def delete_donor(donor_id):

    donor = Donor.query.get(donor_id)

    if donor is None:
        return False

    db.session.delete(donor)
    db.session.commit()

    return True


# ====================================================
# DELETE PATIENT
# ====================================================

def delete_patient(patient_id):

    patient = Patient.query.get(patient_id)

    if patient is None:
        return False

    db.session.delete(patient)
    db.session.commit()

    return True


# ====================================================
# DELETE USER
# ====================================================

def delete_user(user_id):

    user = User.query.get(user_id)

    if user is None:
        return False

    db.session.delete(user)
    db.session.commit()

    return True


# ====================================================
# DELETE DONATION
# ====================================================

def delete_donation(donation_id):

    donation = Donation.query.get(donation_id)

    if donation is None:
        return False

    db.session.delete(donation)
    db.session.commit()

    return True


# ====================================================
# DELETE MATCH
# ====================================================

def delete_match(match_id):

    match = DonorMatch.query.get(match_id)

    if match is None:
        return False

    db.session.delete(match)
    db.session.commit()

    return True
# ====================================================
# REPORT DATA
# ====================================================

def donor_report():

    donors = Donor.query.order_by(
        Donor.donor_id
    ).all()

    report = []

    for donor in donors:

        report.append({

            "Donor ID": donor.donor_id,
            "Blood Group": donor.blood_group,
            "Age": donor.age,
            "Phone": donor.phone,
            "Availability": donor.availability,
            "Reliability Score": donor.reliability_score,
            "Donation Count": donor.donation_count

        })

    return report


def patient_report():

    patients = Patient.query.order_by(
        Patient.patient_id
    ).all()

    report = []

    for patient in patients:

        report.append({

            "Patient ID": patient.patient_id,
            "Blood Group": patient.blood_group,
            "Age": patient.age,
            "Hospital": patient.hospital_name,
            "Phone": patient.phone

        })

    return report


def request_report():

    requests = BloodRequest.query.order_by(
        BloodRequest.request_id
    ).all()

    report = []

    for req in requests:

        report.append({

            "Request ID": req.request_id,
            "Blood Group": req.blood_group,
            "Units": req.units_needed,
            "Status": req.status,
            "Emergency": req.emergency_level,
            "Hospital": req.hospital_name

        })

    return report


def donation_report():

    donations = Donation.query.order_by(
        Donation.donation_id
    ).all()

    report = []

    for donation in donations:

        report.append({

            "Donation ID": donation.donation_id,
            "Donor ID": donation.donor_id,
            "Patient ID": donation.patient_id,
            "Units": donation.units_donated,
            "Date": str(donation.donation_date),
            "Status": donation.donation_status

        })

    return report