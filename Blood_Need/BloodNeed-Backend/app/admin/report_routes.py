from io import StringIO

from flask import Blueprint, make_response
from flask_jwt_extended import jwt_required

from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
report_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/api/admin/reports"
)
@report_bp.route("/donors")
@jwt_required()
def donor_report():

    output = StringIO()

    output.write(
        "Donor ID,Name,Blood Group,Phone,Donations,Reliability\n"
    )

    donors = Donor.query.all()

    for donor in donors:

        data = donor.to_dict()

        output.write(

            f"{donor.donor_id},"

            f"{data['full_name']},"

            f"{donor.blood_group},"

            f"{data['phone']},"

            f"{donor.total_donations},"

            f"{donor.reliability_score}\n"

        )

    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = \
        "attachment; filename=donor_report.csv"

    response.headers["Content-Type"] = "text/csv"

    return response
@report_bp.route("/patients")
@jwt_required()
def patient_report():

    output = StringIO()

    output.write(
        "Patient ID,Name,Phone,Blood Group\n"
    )

    patients = Patient.query.all()

    for patient in patients:

        data = patient.to_dict()

        output.write(

            f"{patient.patient_id},"

            f"{data['full_name']},"

            f"{data['phone']},"

            f"{patient.blood_group}\n"

        )

    response = make_response(
        output.getvalue()
    )

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=patient_report.csv"

    response.headers[
        "Content-Type"
    ] = "text/csv"

    return response
@report_bp.route("/requests")
@jwt_required()
def request_report():

    output = StringIO()

    output.write(
        "Request ID,Blood Group,Units,Hospital,Emergency,Status\n"
    )

    requests = BloodRequest.query.all()

    for req in requests:

        output.write(

            f"{req.request_id},"

            f"{req.blood_group},"

            f"{req.units_needed},"

            f"{req.hospital_name},"

            f"{req.emergency_level},"

            f"{req.status}\n"

        )

    response = make_response(
        output.getvalue()
    )

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=request_report.csv"

    response.headers[
        "Content-Type"
    ] = "text/csv"

    return response
@report_bp.route("/donations")
@jwt_required()
def donation_report():

    output = StringIO()

    output.write(
        "Donation ID,Donor ID,Patient ID,Request ID,Date,Units\n"
    )

    donations = Donation.query.all()

    for donation in donations:

        output.write(

            f"{donation.donation_id},"

            f"{donation.donor_id},"

            f"{donation.patient_id},"

            f"{donation.request_id},"

            f"{donation.donation_date},"

            f"{donation.units_donated}\n"

        )

    response = make_response(
        output.getvalue()
    )

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=donation_report.csv"

    response.headers[
        "Content-Type"
    ] = "text/csv"

    return response