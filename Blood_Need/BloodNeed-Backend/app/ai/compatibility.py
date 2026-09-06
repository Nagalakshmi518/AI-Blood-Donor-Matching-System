COMPATIBILITY = {

    "O-": ["O-"],

    "O+": ["O+", "O-"],

    "A-": ["A-", "O-"],

    "A+": ["A+", "A-", "O+", "O-"],

    "B-": ["B-", "O-"],

    "B+": ["B+", "B-", "O+", "O-"],

    "AB-": [
        "AB-",
        "A-",
        "B-",
        "O-"
    ],

    "AB+": [
        "AB+",
        "AB-",
        "A+",
        "A-",
        "B+",
        "B-",
        "O+",
        "O-"
    ]

}


def is_compatible(
        request_group,
        donor_group
):

    compatible = COMPATIBILITY.get(
        request_group,
        []
    )

    return donor_group in compatible