from math import radians, sin, cos, sqrt, atan2


# ==========================================
# DISTANCE
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):

    if None in [lat1, lon1, lat2, lon2]:
        return 9999

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ==========================================
# BLOOD COMPATIBILITY
# ==========================================

def blood_match(request_group, donor_group):

    compatibility = {

        "O-": ["O-"],

        "O+": ["O-", "O+"],

        "A-": ["O-", "A-"],

        "A+": ["O-", "O+", "A-", "A+"],

        "B-": ["O-", "B-"],

        "B+": ["O-", "O+", "B-", "B+"],

        "AB-": ["O-", "A-", "B-", "AB-"],

        "AB+": [
            "O-",
            "O+",
            "A-",
            "A+",
            "B-",
            "B+",
            "AB-",
            "AB+",
        ],
    }

    return donor_group in compatibility.get(request_group, [])


# ==========================================
# SEARCH RADIUS
# ==========================================

def allowed_radius(level):

    level = level.upper()

    if level == "CRITICAL":
        return 50

    if level == "HIGH":
        return 50

    return 25


# ==========================================
# AI SCORE
# ==========================================

def calculate_score(request, donor):

    # Blood Compatibility
    if not blood_match(request.blood_group, donor.blood_group):
        return 0

    # -----------------------------
    # Distance
    # -----------------------------
    if (
        donor.latitude is not None
        and donor.longitude is not None
        and request.hospital_latitude is not None
        and request.hospital_longitude is not None
    ):

        distance = calculate_distance(
            donor.latitude,
            donor.longitude,
            request.hospital_latitude,
            request.hospital_longitude,
        )

        if distance > allowed_radius(request.emergency_level):
            return 0

    else:
        distance = 0

    score = 0

    # Blood Match
    score += 50

    # Availability
    if donor.availability:
        score += 20

    # Reliability
    score += donor.reliability_score or 0

    # Donation Experience
    score += min(donor.total_donations * 2, 20)

    # Distance Score
    if distance == 0:
        score += 15
    elif distance <= 2:
        score += 30
    elif distance <= 5:
        score += 25
    elif distance <= 10:
        score += 20
    elif distance <= 25:
        score += 10
    else:
        score += 5

    # Emergency Weight
    if request.emergency_level == "CRITICAL":
        score += 25
    elif request.emergency_level == "HIGH":
        score += 20
    elif request.emergency_level == "MEDIUM":
        score += 10

    return round(score, 2)