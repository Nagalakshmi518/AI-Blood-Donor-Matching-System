def validate_patient(data):

    required_fields = [
        "blood_group",
        "age",
        "gender",
        "hospital_name"
    ]

    for field in required_fields:

        if field not in data or data[field] is None:
            return False, f"{field} is required"

    return True, None