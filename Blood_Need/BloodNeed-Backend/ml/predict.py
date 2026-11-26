"""Inference module for UCI Blood Transfusion historical donation tendency."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd

from ml.preprocessing import FEATURE_COLUMNS, ML_DIR

ARTIFACTS_DIR = ML_DIR / "model_artifacts"

HISTORICAL_TARGET_DISCLAIMER = (
    "This prediction estimates historical donation tendency based on the UCI Blood "
    "Transfusion Service Center dataset (March 2007 target). It does NOT predict "
    "emergency request acceptance, real-time donor availability, or response time, "
    "and must not override medical blood-group compatibility or donor eligibility rules."
)


class ModelArtifactNotFoundError(FileNotFoundError):
    """Raised when the trained ML model artifact is missing."""


class InvalidPredictionInputError(ValueError):
    """Raised when prediction inputs fail validation."""


def _validate_numeric_value(name: str, value: Any, *, min_value: float, strict_gt: bool = False) -> float:
    if value is None or isinstance(value, bool):
        raise InvalidPredictionInputError(f"'{name}' must be a valid number.")
    try:
        num = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidPredictionInputError(f"'{name}' must be numeric.") from exc

    if not math.isfinite(num):
        raise InvalidPredictionInputError(f"'{name}' must be finite (not NaN or Inf).")

    if strict_gt:
        if num <= min_value:
            raise InvalidPredictionInputError(f"'{name}' must be > {min_value}.")
    else:
        if num < min_value:
            raise InvalidPredictionInputError(f"'{name}' must be >= {min_value}.")

    return num


def validate_prediction_inputs(
    recency_months: Any,
    frequency_times: Any,
    monetary_cc: Any,
    time_months: Any,
) -> Dict[str, float]:
    """Validate the four UCI RFMT features and domain consistency rules."""
    recency = _validate_numeric_value("recency_months", recency_months, min_value=0.0)
    frequency = _validate_numeric_value("frequency_times", frequency_times, min_value=1.0)
    monetary = _validate_numeric_value("monetary_cc", monetary_cc, min_value=0.0, strict_gt=True)
    time_m = _validate_numeric_value("time_months", time_months, min_value=0.0)

    if time_m < recency:
        raise InvalidPredictionInputError(
            "'time_months' (months since first donation) cannot be less than "
            "'recency_months' (months since last donation)."
        )

    return {
        "recency_months": recency,
        "frequency_times": frequency,
        "monetary_cc": monetary,
        "time_months": time_m,
    }


class BloodDonationPredictor:
    """Loads saved ML artifacts and serves historical donation tendency predictions."""

    def __init__(self, artifacts_dir: str | Path | None = None) -> None:
        self.artifacts_dir = Path(artifacts_dir if artifacts_dir is not None else ARTIFACTS_DIR)
        self._model = None
        self._metadata: Optional[Dict[str, Any]] = None

    def load(self) -> None:
        model_path = self.artifacts_dir / "best_model.joblib"
        metadata_path = self.artifacts_dir / "model_metadata.json"

        if not model_path.exists():
            raise ModelArtifactNotFoundError(
                f"Trained model artifact not found at '{model_path}'. "
                "Run 'python -m ml.train_model' first."
            )

        self._model = joblib.load(model_path)

        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {}

    def _ensure_loaded(self) -> None:
        if self._model is None:
            self.load()

    def get_model_info(self) -> Dict[str, Any]:
        self._ensure_loaded()
        selected = (self._metadata or {}).get("selected_model", {})
        repro = (self._metadata or {}).get("reproducibility", {})
        return {
            "model_key": selected.get("key", type(self._model).__name__),
            "model_name": selected.get("name", type(self._model).__name__),
            "dataset": (self._metadata or {}).get(
                "dataset", "UCI Blood Transfusion Service Center"
            ),
            "target_description": (self._metadata or {}).get(
                "target_meaning",
                "Historical donation indicator (March 2007), not emergency response.",
            ),
            "test_metrics": selected.get("test_metrics"),
            "cv_metrics": selected.get("cv_metrics"),
            "trained_at_utc": repro.get("trained_at_utc"),
            "random_state": repro.get("random_state"),
        }

    def predict(
        self,
        recency_months: Any,
        frequency_times: Any,
        monetary_cc: Any,
        time_months: Any,
    ) -> Dict[str, Any]:
        self._ensure_loaded()
        cleaned = validate_prediction_inputs(
            recency_months=recency_months,
            frequency_times=frequency_times,
            monetary_cc=monetary_cc,
            time_months=time_months,
        )

        features_df = pd.DataFrame(
            [
                [
                    cleaned["recency_months"],
                    cleaned["frequency_times"],
                    cleaned["monetary_cc"],
                    cleaned["time_months"],
                ]
            ],
            columns=FEATURE_COLUMNS,
        )

        predicted_class = int(self._model.predict(features_df)[0])
        probability_donate = None
        probability_not_donate = None
        if hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba(features_df)[0]
            probability_not_donate = round(float(probs[0]), 4)
            probability_donate = round(float(probs[1]), 4)

        return {
            "predicted_class": predicted_class,
            "predicted_label": (
                "Historical Donation Likely (1)"
                if predicted_class == 1
                else "Historical Donation Unlikely (0)"
            ),
            "probability_score": probability_donate,
            "probabilities": {
                "not_donated_0": probability_not_donate,
                "donated_1": probability_donate,
            },
            "input_features": cleaned,
            "model_info": self.get_model_info(),
            "target_scope": "UCI_HISTORICAL_DONATION_BEHAVIOR",
            "disclaimer": HISTORICAL_TARGET_DISCLAIMER,
        }


def predict_historical_donation(
    recency_months: Any,
    frequency_times: Any,
    monetary_cc: Any,
    time_months: Any,
    artifacts_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """Convenience function to validate inputs, load saved artifacts, and predict."""
    predictor = BloodDonationPredictor(artifacts_dir=artifacts_dir)
    return predictor.predict(
        recency_months=recency_months,
        frequency_times=frequency_times,
        monetary_cc=monetary_cc,
        time_months=time_months,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Predict historical blood donation tendency using UCI RFMT features."
    )
    parser.add_argument("--recency", type=float, required=True, help="Months since last donation")
    parser.add_argument("--frequency", type=float, required=True, help="Total number of donations (>=1)")
    parser.add_argument("--monetary", type=float, required=True, help="Total blood donated in c.c. (>0)")
    parser.add_argument("--time", type=float, required=True, help="Months since first donation (>= recency)")
    args = parser.parse_args()

    output = predict_historical_donation(
        recency_months=args.recency,
        frequency_times=args.frequency,
        monetary_cc=args.monetary,
        time_months=args.time,
    )
    print(json.dumps(output, indent=2))
