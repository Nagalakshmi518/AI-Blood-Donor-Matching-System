from app import db

from app.models.donor import Donor
from app.models.user import User


# ====================================================
# CREATE DONOR
# ====================================================

def create_donor(data, user_id):

    # ---------------------------------------------
    # CHECK USER
    # ---------------------------------------------

    user = User.query.get(

        user_id

    )


    if user is None:

        return None


    # ---------------------------------------------
    # CHECK EXISTING DONOR PROFILE
    # ---------------------------------------------

    existing_donor = Donor.query.filter_by(

        user_id=user_id

    ).first()


    if existing_donor:

        return None


    # ---------------------------------------------
    # CREATE DONOR
    # ---------------------------------------------

    donor = Donor(
        user_id=user_id,
        blood_group=data["blood_group"],
        age=data["age"],
        gender=data["gender"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        address=data.get("address"),
        last_donation_date=data.get("last_donation_date"),
        total_donations=0,
        availability=True,
        reliability_score=0.0,
        reward_points=0,
        badge="New Donor"
    )


    db.session.add(

        donor

    )


    db.session.commit()


    return donor


# ====================================================
# GET ALL DONORS
# ====================================================

def get_all_donors():

    return Donor.query.all()


# ====================================================
# GET DONOR BY ID
# ====================================================

def get_donor(donor_id):

    return Donor.query.get(

        donor_id

    )


# ====================================================
# UPDATE DONOR
# ====================================================

def update_donor(

    donor,

    data

):

    allowed_fields = [

        "blood_group",

        "age",

        "gender",

        "weight",

        "latitude",

        "longitude",

        "address"

    ]


    for field in allowed_fields:

        if field in data:

            setattr(

                donor,

                field,

                data[field]

            )

    if donor.latitude is None or donor.longitude is None:

        raise ValueError(
            "Donor location is required."
        )

    db.session.commit()


    return donor


# ====================================================
# DELETE DONOR
# ====================================================

def delete_donor(

    donor

):

    db.session.delete(

        donor

    )

    db.session.commit()