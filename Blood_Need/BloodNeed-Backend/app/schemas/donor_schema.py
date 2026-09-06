def validate_donor(data):

    required_fields = [
        "user_id",
        "blood_group",
        "age",
        "gender"
    ]

    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"{field} is required"

    return True, None