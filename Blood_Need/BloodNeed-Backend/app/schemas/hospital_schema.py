def validate_hospital(data):

    required_fields = [
        "hospital_name",
        "city",
        "state",
        "address",
        "phone"
    ]

    for field in required_fields:

        if field not in data or not data[field]:
            return False, f"{field} is required"

    return True, None