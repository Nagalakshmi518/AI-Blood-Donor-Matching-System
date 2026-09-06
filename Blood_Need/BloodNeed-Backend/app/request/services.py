from app import db

from app.models.blood_request import BloodRequest
from app.models.patient import Patient
from datetime import date, timedelta
from app.models.donation import Donation


# ====================================================
# CREATE BLOOD REQUEST
# ====================================================

def create_request(data):

    # ---------------------------------------------
    # VERIFY PATIENT
    # ---------------------------------------------

    patient = Patient.query.get(
        data["patient_id"]
    )

    if patient is None:


        return None


    # ---------------------------------------------
    # CREATE BLOOD REQUEST
    # ---------------------------------------------

    blood_request = BloodRequest(

        patient_id=data["patient_id"],

        blood_group=data["blood_group"],

        units_needed=data["units_needed"],

        emergency_level=data["emergency_level"],

        hospital_name=data["hospital_name"],

        hospital_latitude=data.get(
            "hospital_latitude"
        ),

        hospital_longitude=data.get(
            "hospital_longitude"
        ),

        notes=data.get(
            "notes"
        )

    )


    # ---------------------------------------------
    # INITIAL REQUEST STATUS
    # ---------------------------------------------

    blood_request.status = "Pending"


    # ---------------------------------------------
    # SAVE REQUEST
    # ---------------------------------------------

    db.session.add(
        blood_request
    )

    db.session.commit()


    return blood_request


# ====================================================
# GET ALL BLOOD REQUESTS
# ====================================================

def get_all_requests():

    return BloodRequest.query.order_by(

        BloodRequest.request_time.desc()

    ).all()


# ====================================================
# GET BLOOD REQUEST BY ID
# ====================================================

def get_request(
    request_id
):

    return BloodRequest.query.get(

        request_id

    )


# ====================================================
# UPDATE BLOOD REQUEST
# ====================================================

def update_request(

    blood_request,

    data

):

    allowed_fields = [

        "blood_group",

        "units_needed",

        "emergency_level",

        "hospital_name",

        "hospital_latitude",

        "hospital_longitude",

        "notes"

    ]


    for key, value in data.items():

        if key in allowed_fields:

            setattr(

                blood_request,

                key,

                value

            )


    db.session.commit()


    return blood_request


# ====================================================
# DELETE BLOOD REQUEST
# ====================================================

def delete_request(

    blood_request

):

    db.session.delete(

        blood_request

    )

    db.session.commit()
# ====================================================
# COMPLETE BLOOD REQUEST
# ====================================================

from app.models.donor_match import DonorMatch
from app.notifications.services import create_notification


def complete_request(request_id):

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:
        return None

    if blood_request.status == "Completed":
        return "already_completed"

    accepted_match = DonorMatch.query.filter_by(
        request_id=request_id,
        donor_response="Accepted"
    ).first()

    if accepted_match is None:
        return False

    donor = accepted_match.donor

    existing_donation = Donation.query.filter_by(request_id=request_id).first()
    if existing_donation:
        if existing_donation.donation_status == "Completed":
            blood_request.status = "Completed"
            db.session.commit()
            return "already_completed"
        existing_donation.donation_status = "Completed"
        existing_donation.donation_date = existing_donation.donation_date or date.today()
        existing_donation.units_donated = existing_donation.units_donated or (blood_request.units_needed or 1)
        donation = existing_donation
    else:
        donation = Donation(
            donor_id=accepted_match.donor_id,
            patient_id=blood_request.patient_id,
            request_id=blood_request.request_id,
            donation_date=date.today(),
            units_donated=blood_request.units_needed or 1,
            donation_status="Completed"
        )
        db.session.add(donation)

    blood_request.status = "Completed"
    accepted_match.donor_response = "Accepted"

    if donor:
        donor.successful_donations = (donor.successful_donations or 0) + 1
        donor.accepted_requests = (donor.accepted_requests or 0) + 1
        donor.total_donations = (donor.total_donations or 0) + 1
        donor.last_donation_date = date.today()
        donor.next_eligible_date = date.today() + timedelta(days=90)
        donor.availability = False
        donor.reliability_score = min((donor.reliability_score or 0) + 5, 100)
        donor.reward_points = (donor.reward_points or 0) + 50

        if donor.total_donations >= 20:
            donor.badge = "Platinum Donor"
        elif donor.total_donations >= 10:
            donor.badge = "Gold Donor"
        elif donor.total_donations >= 5:
            donor.badge = "Silver Donor"
        elif donor.total_donations >= 1:
            donor.badge = "Bronze Donor"
        else:
            donor.badge = "New Donor"

        from app.reward.services import add_reward, check_badges
        add_reward(donor.donor_id, 50, "Successful Blood Donation")
        check_badges(donor)

    patient = Patient.query.get(blood_request.patient_id)
    if patient:
        create_notification({
            "user_id": patient.user_id,
            "title": "Blood Donation Completed",
            "message": f"Your blood request #{blood_request.request_id} has been completed successfully.",
            "notification_type": "SUCCESS",
            "related_request_id": blood_request.request_id
        })

    if donor:
        create_notification({
            "user_id": donor.user_id,
            "title": "Donation Completed",
            "message": "Your blood donation has been marked as completed and reward points have been updated.",
            "notification_type": "SUCCESS",
            "related_request_id": blood_request.request_id
        })

    db.session.commit()

    return blood_request