from datetime import datetime, timedelta, date

from app import db

from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.response_history import ResponseHistory
from app.models.blood_request import BloodRequest
from app.models.donation import Donation

from app.notifications.services import create_notification

from app.matching.services import (
    get_response_window,
    send_request_email_to_donor
)


# ==========================================
# GET MATCH FOR LOGGED-IN DONOR
# ==========================================

def get_match(match_id, user_id):

    return (
        DonorMatch.query
        .join(Donor)
        .filter(
            DonorMatch.match_id == match_id,
            Donor.user_id == int(user_id)
        )
        .first()
    )


# ==========================================
# SAVE RESPONSE HISTORY
# ==========================================

def save_history(match, status, response_time_seconds=0):

    history = ResponseHistory(
        donor_id=match.donor_id,
        request_id=match.request_id,
        response_status=status,
        response_time_seconds=response_time_seconds,
        ai_score=match.ranking_score
    )

    db.session.add(history)


# ==========================================
# ACCEPT BLOOD REQUEST
# ==========================================

def accept_request(match_id, user_id):

    match = get_match(match_id, user_id)

    if match is None:
        return None

    # Check response deadline
    if (
        match.response_deadline
        and datetime.utcnow() > match.response_deadline
    ):
        return None

    # Only pending request can be accepted
    if match.donor_response != "Pending":
        return None

    donor = match.donor

    if donor is None:
        return None

    blood_request = BloodRequest.query.get(
        match.request_id
    )

    if blood_request is None:
        return None

    # --------------------------------------
    # ACCEPT DONOR
    # --------------------------------------

    match.donor_response = "Accepted"

    # Donor temporarily unavailable
    donor.availability = False

    # Update request
    blood_request.status = "Accepted"

    # --------------------------------------
    # CREATE PENDING DONATION
    # --------------------------------------

    donation = Donation(
        donor_id=donor.donor_id,
        patient_id=blood_request.patient_id,
        request_id=blood_request.request_id,
        donation_date=date.today(),
        units_donated=blood_request.units_needed or 1,
        donation_status="Pending"
    )

    db.session.add(donation)

    # --------------------------------------
    # REJECT OTHER WAITING DONORS
    # --------------------------------------

    other_matches = DonorMatch.query.filter(
        DonorMatch.request_id == match.request_id,
        DonorMatch.match_id != match.match_id,
        DonorMatch.donor_response == "Pending"
    ).all()

    for other_match in other_matches:
        other_match.donor_response = "Rejected"

    # --------------------------------------
    # SAVE RESPONSE HISTORY
    # --------------------------------------

    save_history(
        match,
        "Accepted"
    )

    # --------------------------------------
    # NOTIFY PATIENT
    # --------------------------------------

    patient = blood_request.patient

    if patient:

        create_notification({
            "user_id": patient.user_id,
            "title": "Blood Donor Accepted",
            "message": (
                f"A donor has accepted your request for "
                f"{blood_request.blood_group} blood."
            ),
            "notification_type": "SUCCESS",
            "related_request_id": blood_request.request_id,
            "is_read": False
        })

    # --------------------------------------
    # NOTIFY DONOR
    # --------------------------------------

    create_notification({
        "user_id": donor.user_id,
        "title": "Blood Request Accepted",
        "message": (
            f"You accepted the blood request for "
            f"{blood_request.blood_group}. "
            f"Please complete the donation process."
        ),
        "notification_type": "SUCCESS",
        "related_request_id": blood_request.request_id,
        "is_read": False
    })

    db.session.commit()

    print(
        f"Request {blood_request.request_id} "
        f"accepted by donor {donor.donor_id}"
    )

    return match


# ==========================================
# REJECT BLOOD REQUEST
# ==========================================

def reject_request(match_id, user_id):

    match = get_match(match_id, user_id)

    if match is None:
        return None

    # Only pending request can be rejected
    if match.donor_response != "Pending":
        return None

    # --------------------------------------
    # MARK CURRENT DONOR AS REJECTED
    # --------------------------------------

    match.donor_response = "Rejected"

    save_history(
        match,
        "Rejected"
    )

    print(
        f"Donor {match.donor_id} rejected "
        f"request {match.request_id}"
    )

    # --------------------------------------
    # FIND NEXT DONOR
    # --------------------------------------

    next_match = notify_next_donor(match)

    # --------------------------------------
    # NO MORE DONORS -> HOSPITAL FALLBACK
    # --------------------------------------

    if next_match is None:

        print(
            "No more eligible donors."
        )

        print(
            "Checking hospital inventory..."
        )

        blood_request = BloodRequest.query.get(
            match.request_id
        )

        if (
            blood_request
            and blood_request.status not in [
                "Accepted",
                "Completed",
                "Cancelled"
            ]
        ):

            from app.hospital.services import (
                fallback_blood_bank_for_request
            )

            fallback_result = (
                fallback_blood_bank_for_request(
                    blood_request
                )
            )

            print(
                "Hospital fallback result:",
                fallback_result
            )

    db.session.commit()

    return match


# ==========================================
# NOTIFY NEXT BEST DONOR
# ==========================================

def notify_next_donor(current_match):

    # Find next waiting donor
    next_match = (
        DonorMatch.query
        .filter(
            DonorMatch.request_id
            == current_match.request_id,

            DonorMatch.donor_response
            == "Pending",

            DonorMatch.response_deadline.is_(None),

            DonorMatch.match_id
            != current_match.match_id
        )
        .order_by(
            DonorMatch.ranking_score.desc()
        )
        .first()
    )

    # --------------------------------------
    # NO NEXT DONOR
    # --------------------------------------

    if next_match is None:

        print(
            "No next donor available."
        )

        return None

    # --------------------------------------
    # GET BLOOD REQUEST
    # --------------------------------------

    blood_request = BloodRequest.query.get(
        current_match.request_id
    )

    if blood_request is None:
        return None

    # --------------------------------------
    # RESPONSE TIME BASED ON EMERGENCY
    # --------------------------------------

    response_minutes = get_response_window(
        blood_request.emergency_level
    )

    # Activate next donor
    next_match.response_deadline = (
        datetime.utcnow()
        + timedelta(minutes=response_minutes)
    )

    donor = next_match.donor

    if donor is None:
        return None

    print(
        f"Next donor activated: "
        f"{donor.donor_id}"
    )

    # --------------------------------------
    # NOTIFY NEXT DONOR
    # --------------------------------------

    create_notification({
        "user_id": donor.user_id,
        "title": "New Blood Request",
        "message": (
            f"Blood Group: "
            f"{blood_request.blood_group}\n"
            f"Units Required: "
            f"{blood_request.units_needed or 1}\n"
            f"Hospital: "
            f"{blood_request.hospital_name or 'N/A'}\n"
            f"Emergency: "
            f"{blood_request.emergency_level}\n\n"
            f"Please respond within "
            f"{response_minutes} minutes."
        ),
        "notification_type": "INFO",
        "related_request_id": blood_request.request_id,
        "related_match_id": next_match.match_id,
        "is_read": False
    })

    # --------------------------------------
    # SEND EMAIL
    # --------------------------------------

    send_request_email_to_donor(
        donor,
        blood_request,
        response_minutes
    )

    return next_match


# ==========================================
# PROCESS EXPIRED MATCHES
# ==========================================

def process_expired_matches():

    now = datetime.utcnow()

    expired_matches = (
        DonorMatch.query
        .filter(
            DonorMatch.donor_response == "Pending",
            DonorMatch.response_deadline.isnot(None),
            DonorMatch.response_deadline <= now
        )
        .order_by(
            DonorMatch.ranking_score.desc()
        )
        .all()
    )

    processed = []

    for match in expired_matches:

        print(
            f"Match {match.match_id} expired."
        )

        # --------------------------------------
        # MARK AS MISSED
        # --------------------------------------

        match.donor_response = "Missed"

        save_history(
            match,
            "Missed"
        )

        # --------------------------------------
        # TRY NEXT DONOR
        # --------------------------------------

        next_match = notify_next_donor(
            match
        )

        blood_request = BloodRequest.query.get(
            match.request_id
        )

        # --------------------------------------
        # IF NO NEXT DONOR -> HOSPITAL FALLBACK
        # --------------------------------------

        if next_match is None:

            if (
                blood_request
                and blood_request.status not in [
                    "Accepted",
                    "Completed",
                    "Cancelled"
                ]
            ):

                from app.hospital.services import (
                    fallback_blood_bank_for_request
                )

                fallback_result = (
                    fallback_blood_bank_for_request(
                        blood_request
                    )
                )

                print(
                    "Expired match fallback result:",
                    fallback_result
                )

        # --------------------------------------
        # NOTIFY PATIENT
        # --------------------------------------

        if blood_request:

            patient = blood_request.patient

            if patient:

                if next_match:

                    message = (
                        "The previous donor did not respond. "
                        "AI is notifying the next best donor."
                    )

                else:

                    message = (
                        "No more donors are currently available. "
                        "Hospital blood inventory is being checked."
                    )

                create_notification({
                    "user_id": patient.user_id,
                    "title": "Blood Request Update",
                    "message": message,
                    "notification_type": "INFO",
                    "related_request_id":
                        blood_request.request_id,
                    "is_read": False
                })

        processed.append({
            "expired_match_id": match.match_id,
            "next_match_id": (
                next_match.match_id
                if next_match
                else None
            )
        })

    db.session.commit()

    return processed