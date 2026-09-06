def validate_request(data):

    required_fields = [
        "patient_id",
        "blood_group",
        "units_needed",
        "emergency_level",
        "hospital_name"
    ]

    for field in required_fields:

        if field not in data or data[field] in [None, ""]:
            return False, f"{field} is required"

    # Blood Group Validation
    valid_blood_groups = [
        "A+", "A-", "B+", "B-",
        "AB+", "AB-",
        "O+", "O-"
    ]

    if data["blood_group"] not in valid_blood_groups:
        return False, "Invalid blood group"

    # Emergency Level Validation
    valid_levels = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    if data["emergency_level"] not in valid_levels:
        return False, "Invalid emergency level"

    # Units Validation
    if int(data["units_needed"]) <= 0:
        return False, "Units needed must be greater than zero"

    return True, None