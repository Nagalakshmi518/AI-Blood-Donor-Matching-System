from datetime import date, timedelta
from re import match

from app import db

from app.models.donation import Donation
from app.models.donor import Donor
from app.models.blood_request import BloodRequest

from app.reward.services import add_reward
from app.models.patient import Patient
from app.models.donor_match import DonorMatch
from app.notifications.services import create_notification
from app.models.hospital import Hospital
from app.models.hospital_inventory import HospitalInventory


def create_donation(data):

    donor_id = data.get("donor_id")
    patient_id = data.get("patient_id")
    request_id = data.get("request_id")
    
    units_donated = data.get("units_donated")

    # ==========================================
    # Validate Required Fields
    # ==========================================

    if not donor_id:

        return None, "Donor ID is required"


    if not patient_id:

        return None, "Patient ID is required"


    if not request_id:

        return None, "Request ID is required"


    if not units_donated or units_donated <= 0:

        return None, "Units donated must be greater than zero"


    # ==========================================
    # Find Donor
    # ==========================================

    donor = Donor.query.get(donor_id)

    if donor is None:

        return None, "Donor not found"


    # ==========================================
    # Find Blood Request
    # ==========================================

    blood_request = BloodRequest.query.get(request_id)

    if blood_request is None:

        return None, "Blood request not found"


    # ==========================================
    # Prevent Duplicate Donation
    # ==========================================

    existing_donation = Donation.query.filter_by(

        request_id=request_id

    ).first()


    if existing_donation:

        return None, "Donation already recorded for this request"


    # ==========================================
    # Verify Patient
    # ==========================================

    if blood_request.patient_id != patient_id:

        return None, "Patient does not match this blood request"


    # ==========================================
    # Create Donation
    # ==========================================

    donation = Donation(

    donor_id=donor_id,

    patient_id=patient_id,

    request_id=request_id,

    donation_date=data.get(
        "donation_date",
        date.today()
    ),

    units_donated=units_donated,

    donation_status="Completed"

)


    db.session.add(donation)


    # ==========================================
    # Update Donor Information
    # ==========================================

    # Use the actual field used by your Donor model.
    # Your current code uses total_donations.

    donor.total_donations = (

        donor.total_donations or 0

    ) + 1


    donor.last_donation_date = date.today()


    # Donor becomes temporarily unavailable

    donor.availability = False


    # Update reliability score safely

    current_score = (

        donor.reliability_score or 0

    )


    donor.reliability_score = min(

        100,

        current_score + 5

    )


    # ==========================================
    # Update Blood Request
    # ==========================================

    blood_request.status = "Completed"
    match = DonorMatch.query.filter_by(
        donor_id=donor_id,
        request_id=request_id
    ).first()

    if match:
        match.donor_response = "Accepted"

    # ==========================================
    # Add Reward Points
    # ==========================================

    reward = add_reward(
        donor_id=donor.donor_id,
        points=50,
        reason="Successful Blood Donation"
    )

    if reward is None:
        db.session.rollback()
        return None, "Unable to add reward points"

    patient = Patient.query.get(patient_id)

    if patient:
        create_notification({
            "user_id": patient.user_id,
            "message": f"Your blood request for {blood_request.blood_group} has been completed successfully.",
            "type": "SUCCESS",
            "is_read": False,
            "related_request_id": request_id
        })

    create_notification({
        "user_id": donor.user_id,
        "message": "Thank you for donating blood. 50 reward points have been added.",
        "type": "SUCCESS",
        "is_read": False,
        "related_request_id": request_id
    })

    from app.models.user import User

    admins = User.query.filter_by(role="ADMIN").all()

    for admin in admins:
        create_notification({
            "user_id": admin.user_id,
            "title": "Donation Completed",
            "message": f"Donation for Request #{request_id} has been completed.",
            "notification_type": "SUCCESS",
            "related_request_id": request_id
        })

    db.session.commit()

    return donation, None


# =====================================================
# GET ALL DONATIONS
# =====================================================

def get_all_donations():

    return Donation.query.order_by(

        Donation.donation_date.desc()

    ).all()


# =====================================================
# GET DONATION BY ID
# =====================================================

def get_donation(donation_id):

    return Donation.query.get(donation_id)


# =====================================================
# DELETE DONATION
# =====================================================

def delete_donation(donation):

    db.session.delete(donation)

    db.session.commit()
def mark_donation_completed(donation_id):
    donation = Donation.query.get(donation_id)

    if donation is None:
        return None

    if donation.donation_status == "Completed":
        return donation

    donation.donation_status = "Completed"

    donor = Donor.query.get(donation.donor_id)

    if donor:
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

        reward = add_reward(
            donor_id=donor.donor_id,
            points=50,
            reason="Successful Blood Donation"
        )

        if reward is None:
            db.session.rollback()
            return None

    blood_request = BloodRequest.query.get(donation.request_id)

    if blood_request:
        blood_request.status = "Completed"

        hospital = Hospital.query.filter_by(
            hospital_name=blood_request.hospital_name
        ).first()

        if hospital:
            inventory = HospitalInventory.query.filter_by(
                hospital_id=hospital.hospital_id,
                blood_group=blood_request.blood_group
            ).first()

            if inventory:
                inventory.available_units = (
                    inventory.available_units or 0
                ) + donation.units_donated
            else:
                inventory = HospitalInventory(
                    hospital_id=hospital.hospital_id,
                    blood_group=blood_request.blood_group,
                    available_units=donation.units_donated
                )

                db.session.add(inventory)

    patient = Patient.query.get(donation.patient_id)

    if patient:
        create_notification({
            "user_id": patient.user_id,
            "title": "Donation Completed",
            "message": f"Your blood request for {blood_request.blood_group if blood_request else 'blood'} has been completed successfully.",
            "notification_type": "SUCCESS",
            "related_request_id": donation.request_id
        })

    if donor:
        create_notification({
            "user_id": donor.user_id,
            "title": "Donation Completed",
            "message": "Thank you for donating blood. 50 reward points have been added and your next eligible date has been updated.",
            "notification_type": "SUCCESS",
            "related_request_id": donation.request_id
        })

    db.session.commit()

    return donation