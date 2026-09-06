def validate_badge(data):

    required_fields = [
        "donor_id",
        "badge_name"
    ]

    for field in required_fields:

        if field not in data or data[field] is None:
            return False, f"{field} is required"

    return True, None