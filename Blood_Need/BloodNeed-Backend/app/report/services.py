import csv
import io

from app import db
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation


def generate_donor_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Donor ID",
        "Blood Group",
        "Availability",
        "Total Donations",
        "Reliability Score"
    ])

    rows = db.session.query(
        Donor.donor_id,
        Donor.blood_group,
        Donor.availability,
        Donor.total_donations,
        Donor.reliability_score
    ).all()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def generate_patient_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Patient ID",
        "Blood Group",
        "Hospital"
    ])

    rows = db.session.query(
        Patient.patient_id,
        Patient.blood_group,
        Patient.hospital_name
    ).all()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def generate_request_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Request ID",
        "Patient",
        "Blood Group",
        "Units",
        "Status"
    ])

    rows = db.session.query(
        BloodRequest.request_id,
        BloodRequest.patient_id,
        BloodRequest.blood_group,
        BloodRequest.units_needed,
        BloodRequest.status
    ).all()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def generate_donation_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Donation ID",
        "Donor",
        "Patient",
        "Units",
        "Date"
    ])

    rows = db.session.query(
        Donation.donation_id,
        Donation.donor_id,
        Donation.patient_id,
        Donation.units_donated,
        Donation.donation_date
    ).all()

    for row in rows:
        writer.writerow(row)

    return output.getvalue()