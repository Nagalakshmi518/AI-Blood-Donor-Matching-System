from io import StringIO

from flask import Blueprint, make_response
from flask_jwt_extended import jwt_required

from app import db
from app.models.donor import Donor
from app.models.patient import Patient
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.user import User

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

    donors = (
        db.session.query(
            Donor.donor_id,
            User.full_name,
            Donor.blood_group,
            User.phone,
            Donor.total_donations,
            Donor.reliability_score
        )
        .join(User, Donor.user_id == User.user_id)
        .all()
    )

    for donor_id, full_name, blood_group, phone, total_donations, reliability_score in donors:

        output.write(
            f"{donor_id},"
            f"{full_name or ''},"
            f"{blood_group or ''},"
            f"{phone or ''},"
            f"{total_donations},"
            f"{reliability_score}\n"
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

    patients = (
        db.session.query(
            Patient.patient_id,
            User.full_name,
            User.phone,
            Patient.blood_group
        )
        .join(User, Patient.user_id == User.user_id)
        .all()
    )

    for patient_id, full_name, phone, blood_group in patients:

        output.write(
            f"{patient_id},"
            f"{full_name or ''},"
            f"{phone or ''},"
            f"{blood_group or ''}\n"
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

    requests = (
        db.session.query(
            BloodRequest.request_id,
            BloodRequest.blood_group,
            BloodRequest.units_needed,
            BloodRequest.hospital_name,
            BloodRequest.emergency_level,
            BloodRequest.status
        )
        .all()
    )

    for req_id, blood_group, units_needed, hospital_name, emergency_level, status in requests:

        output.write(
            f"{req_id},"
            f"{blood_group},"
            f"{units_needed},"
            f"{hospital_name},"
            f"{emergency_level},"
            f"{status}\n"
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

    donations = (
        db.session.query(
            Donation.donation_id,
            Donation.donor_id,
            Donation.patient_id,
            Donation.request_id,
            Donation.donation_date,
            Donation.units_donated
        )
        .all()
    )

    for don_id, donor_id, patient_id, request_id, donation_date, units_donated in donations:

        output.write(
            f"{don_id},"
            f"{donor_id},"
            f"{patient_id},"
            f"{request_id},"
            f"{donation_date},"
            f"{units_donated}\n"
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