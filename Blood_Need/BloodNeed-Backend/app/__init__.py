import os

from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from apscheduler.schedulers.background import BackgroundScheduler


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


scheduler = BackgroundScheduler()


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    # ==========================================
    # INITIALIZE EXTENSIONS
    # ==========================================

    db.init_app(app)

    migrate.init_app(app, db)

    jwt.init_app(app)

    cors_origins = app.config.get(
        "CORS_ORIGINS",
        ["*"]
    )

    CORS(
        app,
        origins=cors_origins,
        methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS"
        ],
        allow_headers=[
            "Content-Type",
            "Authorization"
        ]
    )
    # ==========================================
    # IMPORT BLUEPRINTS
    # ==========================================

    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp

    from app.donor.routes import donor_bp

    from app.patient.routes import patient_bp

    from app.request.routes import request_bp

    from app.matching.routes import matching_bp

    from app.response.routes import response_bp

    from app.response_history.routes import (
        response_history_bp
    )

    from app.donation.routes import donation_bp

    from app.reward.routes import reward_bp

    from app.badge.routes import badge_bp

    from app.feedback.routes import feedback_bp
    from app.hospital.routes import hospital_bp

    from app.notifications.routes import (
        notification_bp
    )

    from app.dashboard.routes import dashboard_bp
    from app.analytics.routes import analytics_bp
    from app.admin.report_routes import report_bp


    # ==========================================
    # REGISTER BLUEPRINTS
    # ==========================================

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    app.register_blueprint(donor_bp)

    app.register_blueprint(patient_bp)

    app.register_blueprint(request_bp)

    app.register_blueprint(matching_bp)

    app.register_blueprint(response_bp)

    app.register_blueprint(response_history_bp)

    app.register_blueprint(donation_bp)

    app.register_blueprint(reward_bp)

    app.register_blueprint(badge_bp)

    app.register_blueprint(feedback_bp)

    app.register_blueprint(notification_bp)

    app.register_blueprint(dashboard_bp)

    app.register_blueprint(analytics_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(hospital_bp, url_prefix="/api/hospitals")

    # ==========================================
    # SCHEDULER JOB
    # ==========================================

    from app.matching.timeout import (
        process_expired_matches
    )


    def check_expired_matches():

        with app.app_context():
            try:
                inspector = db.inspect(db.engine)
                if not inspector.has_table("donor_matches"):
                    return
                process_expired_matches()
            except Exception as exc:
                message = str(exc).lower()
                if (
                    "doesn't exist" in message
                    or "no such table" in message
                    or "1146" in message
                ):
                    return
                raise


    # ==========================================
    # START SCHEDULER
    # ==========================================

    disable_scheduler = app.config.get("DISABLE_SCHEDULER") or os.getenv("DISABLE_SCHEDULER", "").strip().lower() in {"1", "true", "yes", "on"}

    if not disable_scheduler and not scheduler.running:

        scheduler.add_job(

            func=check_expired_matches,

            trigger="interval",

            seconds=30,

            id="process_expired_matches",

            replace_existing=True

        )

        scheduler.start()


    # ==========================================
    # HOME ROUTE
    # ==========================================

    @app.route("/")
    def home():

        return {

            "message":
                "🩸 AI Based Blood Donor Matching API",

            "status":
                "Running"

        }


    return app