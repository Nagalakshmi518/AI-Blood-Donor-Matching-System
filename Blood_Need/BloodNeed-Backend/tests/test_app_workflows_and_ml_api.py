"""Integration tests verifying existing BloodNeed workflows and isolated ML research API."""

from __future__ import annotations

import os
import unittest
from datetime import date, datetime, timedelta

# Configure isolated in-memory SQLite DB before importing app
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["DISABLE_SCHEDULER"] = "True"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-at-least-32-bytes"
os.environ["SECRET_KEY"] = "test-app-secret-key"

from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.ai.compatibility import is_compatible
from app.ai.ranking import blood_match, calculate_score
from app.matching.services import find_matching_donors, is_donor_eligible
from app.matching.timeout import process_expired_matches
from app.models.blood_request import BloodRequest
from app.models.donor import Donor
from app.models.donor_match import DonorMatch
from app.models.hospital import Hospital
from app.models.hospital_inventory import HospitalInventory
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.user import User
from app.response.services import accept_request, reject_request


class TestExistingWorkflowsAndMLResearchAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_user(self, email: str, phone: str, role: str, name: str = "Test User") -> User:
        user = User(
            full_name=name,
            email=email,
            phone=phone,
            password=generate_password_hash("Passw0rd!"),
            role=role,
            active=True,
            is_email_verified=True,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def test_blood_compatibility_rules_intact(self):
        self.assertTrue(is_compatible("AB+", "O-"))
        self.assertTrue(is_compatible("A+", "O+"))
        self.assertFalse(is_compatible("O-", "O+"))
        self.assertFalse(is_compatible("A-", "A+"))
        self.assertTrue(blood_match("B+", "B-"))
        self.assertFalse(blood_match("O+", "A+"))

    def test_donor_eligibility_and_cooldown_rules(self):
        user = self._create_user("elig@example.com", "9000000001", "DONOR")
        donor = Donor(
            user_id=user.user_id,
            blood_group="O-",
            age=26,
            gender="Male",
            weight=68.0,
            latitude=12.9716,
            longitude=77.5946,
            availability=True,
            last_donation_date=date.today() - timedelta(days=30),
        )
        db.session.add(donor)
        db.session.commit()

        # Inside 90-day cooldown -> ineligible
        self.assertFalse(is_donor_eligible(donor, user=user))

        # Past 90-day cooldown -> eligible
        donor.last_donation_date = date.today() - timedelta(days=100)
        db.session.commit()
        self.assertTrue(is_donor_eligible(donor, user=user))

        # Unavailable -> ineligible
        donor.availability = False
        db.session.commit()
        self.assertFalse(is_donor_eligible(donor, user=user))

    def test_matching_notification_escalation_and_hospital_fallback_workflow(self):
        # Create patient
        patient_user = self._create_user("patient@example.com", "9000000010", "PATIENT", "Patient One")
        patient = Patient(
            user_id=patient_user.user_id,
            blood_group="A+",
            age=35,
            gender="Female",
            hospital_name="City Care Hospital",
            latitude=12.9716,
            longitude=77.5946,
        )
        db.session.add(patient)

        # Create two compatible donors (one closer/higher reliability, one backup) and one incompatible donor
        d1_user = self._create_user("donor1@example.com", "9000000011", "DONOR", "Donor One")
        d2_user = self._create_user("donor2@example.com", "9000000012", "DONOR", "Donor Two")
        d3_user = self._create_user("donor3@example.com", "9000000013", "DONOR", "Donor Incompat")

        d1 = Donor(
            user_id=d1_user.user_id,
            blood_group="O+",
            age=27,
            gender="Male",
            weight=70.0,
            latitude=12.9720,
            longitude=77.5950,
            availability=True,
            reliability_score=9.0,
            total_donations=5,
        )
        d2 = Donor(
            user_id=d2_user.user_id,
            blood_group="A+",
            age=30,
            gender="Male",
            weight=72.0,
            latitude=12.9900,
            longitude=77.6100,
            availability=True,
            reliability_score=4.0,
            total_donations=1,
        )
        d3 = Donor(
            user_id=d3_user.user_id,
            blood_group="B+",
            age=28,
            gender="Male",
            weight=65.0,
            latitude=12.9716,
            longitude=77.5946,
            availability=True,
            reliability_score=10.0,
            total_donations=10,
        )
        db.session.add_all([d1, d2, d3])

        # Create hospital with inventory fallback
        hosp_user = self._create_user("hosp@example.com", "9000000014", "HOSPITAL", "City Care Admin")
        hospital = Hospital(
            user_id=hosp_user.user_id,
            hospital_name="City Care Hospital",
            address="MG Road",
            latitude=12.9716,
            longitude=77.5946,
            is_active=True,
        )
        db.session.add(hospital)
        db.session.commit()

        inv = HospitalInventory(
            hospital_id=hospital.hospital_id,
            blood_group="A+",
            available_units=4,
        )
        db.session.add(inv)

        req = BloodRequest(
            patient_id=patient.patient_id,
            hospital_id=hospital.hospital_id,
            blood_group="A+",
            units_needed=2,
            emergency_level="CRITICAL",
            hospital_name="City Care Hospital",
            hospital_latitude=12.9716,
            hospital_longitude=77.5946,
            status="Pending",
        )
        db.session.add(req)
        db.session.commit()

        # Incompatible donor receives score 0
        self.assertEqual(calculate_score(req, d3), 0)

        # Match donors: only d1 and d2 should match, d1 ranked first and notified
        matches = find_matching_donors(req)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["donor"].donor_id, d1.donor_id)

        db_matches = (
            DonorMatch.query.filter_by(request_id=req.request_id)
            .order_by(DonorMatch.ranking_score.desc())
            .all()
        )
        self.assertEqual(len(db_matches), 2)
        self.assertIsNotNone(db_matches[0].response_deadline)
        self.assertIsNone(db_matches[1].response_deadline)

        # First donor rejects -> second donor escalated & activated
        reject_request(db_matches[0].match_id, d1_user.user_id)
        db.session.refresh(db_matches[1])
        self.assertIsNotNone(db_matches[1].response_deadline)

        # Force timeout on second donor -> triggers hospital inventory fallback
        db_matches[1].response_deadline = datetime.utcnow() - timedelta(minutes=5)
        db.session.commit()
        processed = process_expired_matches()
        self.assertEqual(len(processed), 1)

        db.session.refresh(req)
        db.session.refresh(inv)
        self.assertEqual(req.status, "Completed")
        self.assertEqual(req.fulfillment_source, "HOSPITAL_INVENTORY")
        self.assertEqual(inv.available_units, 2)
        self.assertGreaterEqual(Notification.query.count(), 2)

    def test_accept_request_workflow_intact(self):
        patient_user = self._create_user("pat2@example.com", "9000000020", "PATIENT", "Patient Two")
        patient = Patient(
            user_id=patient_user.user_id,
            blood_group="O+",
            age=29,
            gender="Male",
            hospital_name="Metro Hospital",
            latitude=12.9716,
            longitude=77.5946,
        )
        donor_user = self._create_user("don2@example.com", "9000000021", "DONOR", "Donor Accept")
        donor = Donor(
            user_id=donor_user.user_id,
            blood_group="O+",
            age=25,
            gender="Female",
            weight=58.0,
            latitude=12.9720,
            longitude=77.5950,
            availability=True,
            reliability_score=8.0,
            total_donations=2,
        )
        db.session.add_all([patient, donor])
        db.session.commit()

        req = BloodRequest(
            patient_id=patient.patient_id,
            blood_group="O+",
            units_needed=1,
            emergency_level="HIGH",
            hospital_name="Metro Hospital",
            hospital_latitude=12.9716,
            hospital_longitude=77.5946,
            status="Matched",
        )
        db.session.add(req)
        db.session.commit()

        matches = find_matching_donors(req)
        self.assertEqual(len(matches), 1)
        match = DonorMatch.query.filter_by(request_id=req.request_id).first()
        accepted = accept_request(match.match_id, donor_user.user_id)
        self.assertIsNotNone(accepted)
        db.session.refresh(req)
        db.session.refresh(donor)
        self.assertEqual(req.status, "Accepted")
        self.assertFalse(donor.availability)

    def test_ml_research_blueprint_registered(self):
        self.assertIn("ml_research", self.app.blueprints)
        rules = {rule.rule for rule in self.app.url_map.iter_rules()}
        self.assertIn("/api/ml-research/status", rules)
        self.assertIn("/api/ml-research/schema-gap", rules)
        self.assertIn("/api/ml-research/predict", rules)

    def test_ml_research_endpoints(self):
        user = self._create_user("admin@example.com", "9000000030", "ADMIN", "Admin User")
        token = create_access_token(identity=str(user.user_id))
        headers = {"Authorization": f"Bearer {token}"}

        # Unauthenticated request denied
        unauth = self.client.get("/api/ml-research/status")
        self.assertEqual(unauth.status_code, 401)

        # Status endpoint
        status_res = self.client.get("/api/ml-research/status", headers=headers)
        self.assertEqual(status_res.status_code, 200)
        status_json = status_res.get_json()
        self.assertTrue(status_json["available"])
        self.assertFalse(status_json["schema_gap"]["operational_integration_enabled"])
        self.assertIn("historical donation", status_json["disclaimer"].lower())
        self.assertEqual(status_json["selected_model"]["key"], "logistic_regression_balanced")
        self.assertGreaterEqual(len(status_json["all_models"]), 2)

        # Schema gap endpoint
        gap_res = self.client.get("/api/ml-research/schema-gap", headers=headers)
        self.assertEqual(gap_res.status_code, 200)
        gap_json = gap_res.get_json()
        self.assertFalse(gap_json["operational_integration_enabled"])
        uci_features = {item["uci_feature"] for item in gap_json["field_mapping_gaps"]}
        self.assertTrue({"Time (months)", "Monetary (c.c. blood)", "Frequency (times)", "Recency (months)"}.issubset(uci_features))
        self.assertTrue(len(gap_json["future_data_requirements"]) >= 1)

        # Valid prediction endpoint
        pred_res = self.client.post(
            "/api/ml-research/predict",
            headers=headers,
            json={
                "recency_months": 2,
                "frequency_times": 6,
                "monetary_cc": 1500,
                "time_months": 16,
            },
        )
        self.assertEqual(pred_res.status_code, 200)
        pred_json = pred_res.get_json()
        self.assertIn(pred_json["predicted_class"], (0, 1))
        self.assertIsNotNone(pred_json["probability_score"])
        self.assertEqual(pred_json["target_scope"], "UCI_HISTORICAL_DONATION_BEHAVIOR")
        self.assertIn("historical donation", pred_json["disclaimer"].lower())
        self.assertIn("not predict emergency", pred_json["disclaimer"].lower())

        # Invalid prediction payloads return 400
        invalid_payloads = [
            None,
            [],
            {"recency_months": 2},
            {"recency_months": 20, "frequency_times": 2, "monetary_cc": 500, "time_months": 5},
            {"recency_months": -1, "frequency_times": 2, "monetary_cc": 500, "time_months": 5},
            {"recency_months": 2, "frequency_times": 0, "monetary_cc": 500, "time_months": 5},
            {"recency_months": 2, "frequency_times": 2, "monetary_cc": 0, "time_months": 5},
            {"recency_months": True, "frequency_times": 2, "monetary_cc": 500, "time_months": 5},
            {"recency_months": "bad", "frequency_times": 2, "monetary_cc": 500, "time_months": 5},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                if payload is None:
                    res = self.client.post("/api/ml-research/predict", headers=headers)
                else:
                    res = self.client.post("/api/ml-research/predict", headers=headers, json=payload)
                self.assertEqual(res.status_code, 400)

    def test_ml_research_handles_missing_artifacts_without_affecting_matching(self):
        import tempfile
        from unittest.mock import patch

        user = self._create_user("admin2@example.com", "9000000031", "ADMIN", "Admin Two")
        token = create_access_token(identity=str(user.user_id))
        headers = {"Authorization": f"Bearer {token}"}

        with tempfile.TemporaryDirectory() as empty_dir:
            with patch("app.ml_research.routes.ARTIFACTS_DIR", empty_dir), patch(
                "ml.predict.ARTIFACTS_DIR", empty_dir
            ):
                # Also simulate metadata present without best_model.joblib
                with open(os.path.join(empty_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
                    f.write("{}")

                status_res = self.client.get("/api/ml-research/status", headers=headers)
                self.assertEqual(status_res.status_code, 503)
                self.assertFalse(status_res.get_json()["available"])

                pred_res = self.client.post(
                    "/api/ml-research/predict",
                    headers=headers,
                    json={
                        "recency_months": 2,
                        "frequency_times": 6,
                        "monetary_cc": 1500,
                        "time_months": 16,
                    },
                )
                self.assertEqual(pred_res.status_code, 503)

                # Core compatibility & matching remain unaffected
                self.assertTrue(is_compatible("A+", "O+"))


if __name__ == "__main__":
    unittest.main()
