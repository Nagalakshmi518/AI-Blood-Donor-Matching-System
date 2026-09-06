def validate_donation(data):

    required = [

        "donor_id",

        "patient_id",

        "request_id"

    ]

    for field in required:

        if field not in data:

            return False, f"{field} is required"

    return True, None