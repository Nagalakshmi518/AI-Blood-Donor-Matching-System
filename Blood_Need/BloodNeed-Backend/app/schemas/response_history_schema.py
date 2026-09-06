def validate_history(data):

    required_fields = [
        "donor_id",
        "request_id",
        "response_status",
        "response_time_seconds"
    ]

    for field in required_fields:

        if field not in data or data[field] is None:
            return False, f"{field} is required"

    return True, None