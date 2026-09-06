from datetime import date, datetime, timedelta

from app import db

from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.patient import Patient
from app.models.user import User

from app.notifications.services import create_notification

from app.ai.ranking import (
    calculate_score,
    calculate_distance,
    allowed_radius
)


# ==========================================
# DONATION COOLDOWN
# ==========================================

DONATION_COOLDOWN_DAYS = 90


def send_request_email_to_donor(donor, blood_request, response_minutes):
    if donor is None:
        return

    user = User.query.get(donor.user_id) if donor.user_id else None
    if user is None or not getattr(user, "email", None):
        return

    body = (
        "You have received a new blood donation request.\n\n"
        f"Blood Group: {blood_request.blood_group}\n"
        f"Units Required: {blood_request.units_needed or 1}\n"
        f"Hospital: {blood_request.hospital_name or 'N/A'}\n"
        f"Emergency: {blood_request.emergency_level or 'N/A'}\n\n"
        "Please log in to BloodNeed to accept or reject this request."
    )

    try:
        from app.utils.email_service import send_email
        send_email(
            user.email,
            subject="BloodNeed - New Blood Request",
            body=body,
        )
    except Exception as exc:
        print(f"[email-warning] donor request email failed for donor {donor.donor_id}: {exc}")


# ==========================================
# RESPONSE TIME BASED ON EMERGENCY
# ==========================================
def get_response_window(emergency_level):

    if emergency_level == "CRITICAL":
        return 15

    elif emergency_level == "HIGH":
        return 30

    elif emergency_level == "MEDIUM":
        return 60

    else:
        return 120



# ==========================================
# CHECK DONOR ELIGIBILITY
# ==========================================

def is_donor_eligible(donor, blood_request=None):

    if donor is None:
        return False

    # Donor must be available
    if donor.availability is not True:
        return False

    user = User.query.get(donor.user_id) if donor.user_id else None
    if user is None:
        return False

    if user.role != "DONOR":
        return False

    if user.active is not True:
        return False

    if donor.latitude is None or donor.longitude is None:
        return False

    if donor.next_eligible_date and date.today() < donor.next_eligible_date:
        return False

    # Donor cooldown period
    if donor.last_donation_date:

        eligible_date = (
            donor.last_donation_date
            + timedelta(
                days=DONATION_COOLDOWN_DAYS
            )
        )

        if date.today() < eligible_date:
            return False

    if blood_request is not None:
        existing_match = DonorMatch.query.filter_by(
            request_id=blood_request.request_id,
            donor_id=donor.donor_id
        ).first()

        if existing_match is not None:
            return False

    return True

# ==========================================
# FIND MATCHING DONORS
# ==========================================
def find_matching_donors(blood_request):
    print("==========================================")
    print("STARTING DONOR MATCHING")
    print("Request ID:", blood_request.request_id)
    print("Request Blood:", blood_request.blood_group)
    print("Hospital Lat:", blood_request.hospital_latitude)
    print("Hospital Lon:", blood_request.hospital_longitude)
    print("==========================================")

    # --------------------------------------
    # Remove old matches for this request
    # --------------------------------------
    DonorMatch.query.filter_by(
        request_id=blood_request.request_id
    ).delete(
        synchronize_session=False
    )

    db.session.commit()

    # --------------------------------------
    # Get all donors
    # --------------------------------------
    donors = Donor.query.all()

    print("Total donors found:", len(donors))

    matched = []

    # --------------------------------------
    # Filter and rank donors
    # --------------------------------------
    for donor in donors:

        print("--------------------------------")
        print("Checking Donor:", donor.donor_id)
        print("Blood:", donor.blood_group)
        print("Available:", donor.availability)
        print("Lat:", donor.latitude)
        print("Lon:", donor.longitude)

        # Check eligibility
        if not is_donor_eligible(donor, blood_request):
            print("Donor not eligible:", donor.donor_id)
            continue

        # Calculate AI ranking score
        score = calculate_score(
            blood_request,
            donor
        )

        print("Score:", score)

        if score <= 0:
            print("Score is zero. Skipping donor:", donor.donor_id)
            continue

        # --------------------------------------
        # Distance Calculation
        # --------------------------------------
        if (
            donor.latitude is not None
            and donor.longitude is not None
            and blood_request.hospital_latitude is not None
            and blood_request.hospital_longitude is not None
        ):

            distance = calculate_distance(
                donor.latitude,
                donor.longitude,
                blood_request.hospital_latitude,
                blood_request.hospital_longitude
            )

            print("Distance:", distance)

            radius = allowed_radius(
                blood_request.emergency_level
            )

            print("Allowed Radius:", radius)

            if distance > radius:
                print(
                    "Donor outside allowed radius:",
                    donor.donor_id
                )
                continue

        else:
            distance = 0

        # --------------------------------------
        # Response Probability
        # --------------------------------------
        response_probability = round(
            min(
                100,
                (donor.reliability_score * 0.7)
                + (donor.total_donations * 3)
            ),
            2
        )

        matched.append({
            "donor": donor,
            "score": score,
            "distance": distance,
            "probability": response_probability
        })

        print(
            "MATCH FOUND:",
            donor.donor_id
        )

    # --------------------------------------
    # Sort donors by ranking score
    # --------------------------------------
    matched.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    print("Total matched donors:", len(matched))

    # --------------------------------------
    # No eligible donors
    # --------------------------------------
    if not matched:
        print("No eligible donors found.")
        return []

    # --------------------------------------
    # Response time based on emergency
    # --------------------------------------
    response_minutes = get_response_window(
        blood_request.emergency_level
    )

    now = datetime.utcnow()

    # --------------------------------------
    # Keep top 10 donors
    # --------------------------------------
    matched = matched[:10]

    # ==========================================
    # CREATE MATCH RECORDS
    # ==========================================
    for index, item in enumerate(matched):

        donor = item["donor"]

        # First-ranked donor gets response deadline
        if index == 0:

            response_deadline = (
                now + timedelta(
                    minutes=response_minutes
                )
            )

        else:

            response_deadline = None

        match = DonorMatch(
            request_id=blood_request.request_id,
            donor_id=donor.donor_id,
            distance_km=item["distance"],
            response_probability=item["probability"],
            ranking_score=item["score"],
            donor_response="Pending",
            response_deadline=response_deadline
        )

        db.session.add(match)

        print(
            "Creating DonorMatch:",
            donor.donor_id
        )

        # --------------------------------------
        # Notify ONLY first-ranked donor
        # --------------------------------------
        if index == 0:

            patient = Patient.query.get(
                blood_request.patient_id
            )

            user = (
                User.query.get(patient.user_id)
                if patient
                else None
            )

            if user:

                create_notification({
                    "user_id": donor.user_id,
                    "title": "New Blood Request",
                    "message": (
                        f"{user.full_name} needs "
                        f"{blood_request.blood_group} blood at "
                        f"{blood_request.hospital_name}. "
                        f"Please respond within "
                        f"{response_minutes} minutes."
                    ),
                    "notification_type": "INFO",
                    "is_read": False
                })

                send_request_email_to_donor(
                    donor,
                    blood_request,
                    response_minutes
                )

    # --------------------------------------
    # SAVE ALL MATCHES
    # --------------------------------------
    db.session.commit()

    print("==========================================")
    print("MATCHING COMPLETED SUCCESSFULLY")
    print("Matches created:", len(matched))
    print("==========================================")

    return matched