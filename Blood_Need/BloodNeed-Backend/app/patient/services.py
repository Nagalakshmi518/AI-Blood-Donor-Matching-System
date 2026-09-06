from app import db
from app.models.patient import Patient

from app.models.user import User

def create_patient(data):

    existing = Patient.query.filter_by(
        user_id=data["user_id"]
    ).first()

    if existing:
        return existing

    patient = Patient(
        user_id=data["user_id"],
        blood_group=data["blood_group"],
        age=data["age"],
        gender=data["gender"],
        hospital_name=data["hospital_name"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude")
    )

    db.session.add(patient)
    db.session.commit()

    return patient

def get_all_patients():

    return Patient.query.all()


def get_patient(patient_id):

    return Patient.query.get(patient_id)


def update_patient(patient, data):

    allowed_fields = [

        "blood_group",

        "age",

        "gender",

        "hospital_name",

        "latitude",

        "longitude"

    ]

    for field in allowed_fields:

        if field in data:
            setattr(patient, field, data[field])

    db.session.commit()

    return patient


def delete_patient(patient):

    db.session.delete(patient)

    db.session.commit()