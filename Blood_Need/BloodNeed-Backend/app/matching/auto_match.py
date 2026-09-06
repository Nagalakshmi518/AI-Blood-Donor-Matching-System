from app.matching.services import find_matching_donors


def generate_matches(blood_request):
    """
    Generate donor matches for a blood request.

    The matching service is responsible for:
    - Blood-group compatibility
    - Donor availability
    - Donation cooldown eligibility
    - Distance calculation
    - AI-based multi-factor ranking
    - Emergency-level prioritization
    """

    matches = find_matching_donors(blood_request)

    return matches