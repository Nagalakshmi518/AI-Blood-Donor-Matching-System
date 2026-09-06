def validate_register(data):

    required_fields = [
        "full_name",
        "email",
        "phone",
        "password",
        "role"
    ]

    for field in required_fields:

        if field not in data or not data[field]:
            return False, f"{field} is required"

    return True, None


def validate_login(data):

    required_fields = [
        "email",
        "password"
    ]

    for field in required_fields:

        if field not in data or not data[field]:
            return False, f"{field} is required"

    return True, None