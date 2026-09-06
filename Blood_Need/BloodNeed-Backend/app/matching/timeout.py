from datetime import datetime, timedelta

from app import db

from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.blood_request import BloodRequest

from app.response_history.services import create_history
from app.notifications.services import create_notification

from app.matching.services import (
    is_donor_eligible,
    get_response_window
)

from app.ai.ranking import (
    calculate_score,
    calculate_distance,
    allowed_radius
)


# ==========================================
# FIND NEXT ELIGIBLE DONOR
# ==========================================

def find_next_donor(blood_request):

    # Donors who already received a match for this request
    already_matched_donor_ids = [

        donor_id

        for (
            donor_id,
        ) in db.session.query(
            DonorMatch.donor_id
        ).filter_by(
            request_id=blood_request.request_id
        ).all()

    ]


    donors = Donor.query.all()

    candidates = []


    for donor in donors:

        # Skip donors who already received this request
        if donor.donor_id in already_matched_donor_ids:

            continue


        # Check availability + donation cooldown
        if not is_donor_eligible(donor, blood_request):

            continue


        # Calculate AI ranking score
        score = calculate_score(

            blood_request,

            donor

        )


        if score <= 0:

            continue


        # Calculate distance
        distance = calculate_distance(

            donor.latitude,

            donor.longitude,

            blood_request.hospital_latitude,

            blood_request.hospital_longitude

        )

        if distance > allowed_radius(blood_request.emergency_level):
            continue

        # Calculate response probability
        response_probability = min(

            100,

            round(

                (donor.reliability_score or 0)

                + (

                    (donor.total_donations or 0)

                    * 2

                ),

                2

            )

        )


        candidates.append({

            "donor": donor,

            "score": score,

            "distance": distance,

            "probability": response_probability

        })


    # Sort by highest ranking score
    candidates.sort(

        key=lambda item: item["score"],

        reverse=True

    )


    if not candidates:

        return None


    return candidates[0]


# ==========================================
# PROCESS EXPIRED DONOR MATCHES
# ==========================================

def process_expired_matches():

    now = datetime.utcnow()


    expired_matches = DonorMatch.query.filter(

        DonorMatch.donor_response == "Pending",

        DonorMatch.response_deadline <= now

    ).all()


    processed = []


    for match in expired_matches:

        # ==========================================
        # GET BLOOD REQUEST
        # ==========================================

        blood_request = BloodRequest.query.get(

            match.request_id

        )


        if blood_request is None:

            continue


        # ==========================================
        # MARK CURRENT DONOR AS MISSED
        # ==========================================

        match.donor_response = "Missed"


        # ==========================================
        # RESPONSE HISTORY
        # ==========================================

        create_history({

            "donor_id": match.donor_id,

            "request_id": match.request_id,

            "response_status": "Missed",

            "response_time_seconds": 0,

            "ai_score": match.ranking_score

        })


        # ==========================================
        # FIND NEXT DONOR
        # ==========================================

        next_donor_data = find_next_donor(

            blood_request

        )


        if next_donor_data:

            donor = next_donor_data["donor"]


            response_minutes = get_response_window(

                blood_request.emergency_level

            )


            response_deadline = (

                now

                + timedelta(

                    minutes=response_minutes

                )

            )


            # ==========================================
            # CREATE NEW MATCH
            # ==========================================

            new_match = DonorMatch(

                request_id=blood_request.request_id,

                donor_id=donor.donor_id,

                distance_km=next_donor_data["distance"],

                response_probability=(

                    next_donor_data["probability"]

                ),

                ranking_score=next_donor_data["score"],

                donor_response="Pending",

                response_deadline=response_deadline

            )


            db.session.add(new_match)


            # ==========================================
            # NOTIFY NEXT DONOR
            # ==========================================

            create_notification({

                "user_id": donor.user_id,

                "title": "New Blood Request",

                "message": (

                    f"{blood_request.emergency_level} "

                    f"blood request for "

                    f"{blood_request.blood_group}. "

                    f"Please respond within "

                    f"{response_minutes} minutes."

                ),

                "notification_type": "INFO"

            })


        else:
            # ==========================================
            # NO DONOR LEFT: keep request active and use hospital fallback
            # ==========================================
            from app.hospital.services import fallback_blood_bank_for_request

            fallback_blood_bank_for_request(blood_request)


        processed.append(match.match_id)


    db.session.commit()


    return processed