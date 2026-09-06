from flask import Blueprint
from flask import Response

from flask_jwt_extended import jwt_required

from app.report.services import (
    generate_donor_csv,
    generate_patient_csv,
    generate_request_csv,
    generate_donation_csv
)

report_bp = Blueprint(
    "report",
    __name__,
    url_prefix="/api/reports"
)


# ==========================================
# DONOR REPORT
# ==========================================

@report_bp.route(
    "/donors",
    methods=["GET"]
)
@jwt_required()
def donor_report():

    csv_data = generate_donor_csv()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=donors_report.csv"

        }

    )


# ==========================================
# PATIENT REPORT
# ==========================================

@report_bp.route(
    "/patients",
    methods=["GET"]
)
@jwt_required()
def patient_report():

    csv_data = generate_patient_csv()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=patients_report.csv"

        }

    )


# ==========================================
# BLOOD REQUEST REPORT
# ==========================================

@report_bp.route(
    "/requests",
    methods=["GET"]
)
@jwt_required()
def request_report():

    csv_data = generate_request_csv()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=requests_report.csv"

        }

    )


# ==========================================
# DONATION REPORT
# ==========================================

@report_bp.route(
    "/donations",
    methods=["GET"]
)
@jwt_required()
def donation_report():

    csv_data = generate_donation_csv()

    return Response(

        csv_data,

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            "attachment; filename=donations_report.csv"

        }

    )