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



from sqlalchemy.orm import joinedload
from app.ai.ranking import blood_match

# ==========================================
# CHECK DONOR ELIGIBILITY
# ==========================================

def is_donor_eligible(donor, blood_request=None, already_matched_donor_ids=None):

    if donor is None:
        return False

    # Donor must be available
    if donor.availability is not True:
        return False

    user = getattr(donor, "user", None) or (User.query.get(donor.user_id) if donor.user_id else None)
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
        if already_matched_donor_ids is not None:
            if donor.donor_id in already_matched_donor_ids:
                return False
        else:
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
    # Get eligible candidates from DB directly
    # --------------------------------------
    compatible_groups = [
        group for group in ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
        if blood_match(blood_request.blood_group, group)
    ]

    donors = (
        Donor.query
        .join(User, Donor.user_id == User.user_id)
        .options(joinedload(Donor.user))
        .filter(
            Donor.availability == True,
            Donor.blood_group.in_(compatible_groups),
            User.role == "DONOR",
            User.active == True,
            Donor.latitude.isnot(None),
            Donor.longitude.isnot(None)
        )
        .all()
    )

    print("Total compatible donors found:", len(donors))

    already_matched_donor_ids = set()

    matched = []

    # --------------------------------------
    # Filter and rank donors
    # --------------------------------------
    for donor in donors:

        # Check eligibility (cooldown, next_eligible_date, match history)
        if not is_donor_eligible(donor, blood_request, already_matched_donor_ids):
            continue

        # Single distance calculation
        distance = calculate_distance(
            donor.latitude,
            donor.longitude,
            blood_request.hospital_latitude,
            blood_request.hospital_longitude
        )

        radius = allowed_radius(blood_request.emergency_level)
        if distance > radius:
            continue

        # Calculate AI ranking score with precalculated distance
        score = calculate_score(
            blood_request,
            donor,
            precalculated_distance=distance
        )

        if score <= 0:
            continue

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