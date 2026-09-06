def validate_notification(data):

    required_fields = [
        "user_id",
        "title",
        "message"
    ]

    for field in required_fields:

        if field not in data or not data[field]:
            return False, f"{field} is required"

    return True, None