def validate_admin_action(data):

    required_fields = [
        "action"
    ]

    for field in required_fields:

        if field not in data or not data[field]:
            return False, f"{field} is required"

    return True, None