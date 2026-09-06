def validate_feedback(data):

    required_fields = [
        "donor_id",
        "patient_id",
        "rating",
        "comment"
    ]

    for field in required_fields:

        if field not in data or data[field] is None:
            return False, f"{field} is required"

    # Rating Validation
    if not isinstance(data["rating"], int):
        return False, "Rating must be an integer"

    if data["rating"] < 1 or data["rating"] > 5:
        return False, "Rating must be between 1 and 5"

    # Comment Validation
    if not str(data["comment"]).strip():
        return False, "Comment cannot be empty"

    return True, None