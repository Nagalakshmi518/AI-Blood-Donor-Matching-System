import csv
import io

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

    donors = Donor.query.all()

    for donor in donors:

        writer.writerow([
            donor.donor_id,
            donor.blood_group,
            donor.availability,
            donor.total_donations,
            donor.reliability_score
        ])

    return output.getvalue()


def generate_patient_csv():

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Patient ID",
        "Blood Group",
        "Hospital"
    ])

    patients = Patient.query.all()

    for patient in patients:

        writer.writerow([
            patient.patient_id,
            patient.blood_group,
            patient.hospital_name
        ])

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

    requests = BloodRequest.query.all()

    for req in requests:

        writer.writerow([
            req.request_id,
            req.patient_id,
            req.blood_group,
            req.units_required,
            req.status
        ])

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

    donations = Donation.query.all()

    for donation in donations:

        writer.writerow([
            donation.donation_id,
            donation.donor_id,
            donation.patient_id,
            donation.units_donated,
            donation.donation_date
        ])

    return output.getvalue()