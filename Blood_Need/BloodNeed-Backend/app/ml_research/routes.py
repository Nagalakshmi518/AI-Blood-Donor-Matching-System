"""Optional, non-operational ML research endpoints for UCI historical donation analysis."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ml.predict import (
    ARTIFACTS_DIR,
    HISTORICAL_TARGET_DISCLAIMER,
    BloodDonationPredictor,
    InvalidPredictionInputError,
    ModelArtifactNotFoundError,
)

ml_research_bp = Blueprint(
    "ml_research",
    __name__,
    url_prefix="/api/ml-research",
)

SCHEMA_GAP_EXPLANATION = {
    "operational_integration_enabled": False,
    "reason": (
        "The operational Donor schema lacks valid corresponding RFMT fields required by "
        "the UCI Blood Transfusion model, so live donor records are not mapped or scored "
        "during emergency matching."
    ),
    "field_mapping_gaps": [
        {
            "uci_feature": "Recency (months)",
            "bloodneed_status": "Partially available via Donor.last_donation_date, but nullable for new donors.",
        },
        {
            "uci_feature": "Frequency (times)",
            "bloodneed_status": "Donor.total_donations defaults to 0 for new donors; UCI requires >= 1.",
        },
        {
            "uci_feature": "Monetary (c.c. blood)",
            "bloodneed_status": "Not stored in Donor table; Donation records only store integer units_donated within the platform.",
        },
        {
            "uci_feature": "Time (months)",
            "bloodneed_status": "Missing: neither User nor Donor stores first_donation_date or account age.",
        },
        {
            "uci_feature": "Target (donated in March 2007)",
            "bloodneed_status": "Incompatible semantics: measures scheduled historical donation, NOT emergency request acceptance.",
        },
    ],
    "future_data_requirements": [
        "Donor first_donation_date and cumulative lifetime blood volume (c.c.).",
        "Logged DonorMatch / ResponseHistory labels (Accepted vs. Rejected/Missed) across real requests.",
        "Contextual request features: response_time_seconds, distance_km, emergency_level, time_of_day.",
    ],
}


@ml_research_bp.route("/status", methods=["GET"])
@jwt_required()
def ml_research_status():
    """Return saved research model comparison metrics and scope disclaimer."""
    artifacts_path = Path(ARTIFACTS_DIR)
    metadata_path = artifacts_path / "model_metadata.json"
    model_path = artifacts_path / "best_model.joblib"

    if not metadata_path.exists() or not model_path.exists():
        return jsonify({
            "available": False,
            "message": "Research ML artifacts not found. Run 'python -m ml.train_model' to generate them.",
            "disclaimer": HISTORICAL_TARGET_DISCLAIMER,
            "schema_gap": SCHEMA_GAP_EXPLANATION,
        }), 503

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except (OSError, json.JSONDecodeError):
        return jsonify({
            "available": False,
            "message": "Research ML metadata is unreadable. Run 'python -m ml.train_model' to regenerate artifacts.",
            "disclaimer": HISTORICAL_TARGET_DISCLAIMER,
            "schema_gap": SCHEMA_GAP_EXPLANATION,
        }), 503

    return jsonify({
        "available": True,
        "dataset": metadata.get("dataset"),
        "target_meaning": metadata.get("target_meaning"),
        "selected_model": metadata.get("selected_model"),
        "all_models": metadata.get("all_models"),
        "dataset_validation": metadata.get("dataset_validation"),
        "reproducibility": metadata.get("reproducibility"),
        "disclaimer": HISTORICAL_TARGET_DISCLAIMER,
        "schema_gap": SCHEMA_GAP_EXPLANATION,
    }), 200


@ml_research_bp.route("/schema-gap", methods=["GET"])
@jwt_required()
def ml_research_schema_gap():
    """Explain why operational donor records are intentionally decoupled from the UCI model."""
    return jsonify(SCHEMA_GAP_EXPLANATION), 200


@ml_research_bp.route("/predict", methods=["POST"])
@jwt_required()
def ml_research_predict():
    """Predict historical donation tendency from explicit UCI RFMT inputs."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "message": "JSON body with recency_months, frequency_times, monetary_cc, and time_months is required."
        }), 400

    required_fields = [
        "recency_months",
        "frequency_times",
        "monetary_cc",
        "time_months",
    ]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({
            "message": f"Missing required input fields: {', '.join(missing)}"
        }), 400

    predictor = BloodDonationPredictor(artifacts_dir=ARTIFACTS_DIR)
    try:
        result = predictor.predict(
            recency_months=data["recency_months"],
            frequency_times=data["frequency_times"],
            monetary_cc=data["monetary_cc"],
            time_months=data["time_months"],
        )
    except InvalidPredictionInputError as exc:
        return jsonify({"message": str(exc)}), 400
    except ModelArtifactNotFoundError as exc:
        return jsonify({"message": str(exc)}), 503

    return jsonify(result), 200
