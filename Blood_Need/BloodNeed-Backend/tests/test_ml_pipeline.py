"""Unit tests for dataset loading, validation, preprocessing, training, and prediction."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from ml.predict import (
    BloodDonationPredictor,
    InvalidPredictionInputError,
    ModelArtifactNotFoundError,
    predict_historical_donation,
)
from ml.preprocessing import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    load_dataset,
    prepare_features_and_target,
    split_dataset,
    validate_dataset,
)
from ml.train_model import train_and_evaluate


class TestMLDatasetAndPreprocessing(unittest.TestCase):
    def test_dataset_loading_and_validation(self):
        df = load_dataset()
        self.assertEqual(df.shape, (748, 5))
        report = validate_dataset(df)
        self.assertEqual(report["row_count"], 748)
        self.assertEqual(report["feature_count"], 4)
        self.assertEqual(report["class_distribution"]["0_not_donated"], 570)
        self.assertEqual(report["class_distribution"]["1_donated"], 178)
        self.assertTrue(all(v == 0 for v in report["missing_values"].values()))

    def test_missing_dataset_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_dataset("ml/non_existent_dataset.data")

    def test_validation_rejects_corrupted_data(self):
        df = load_dataset()

        missing_col_df = df.drop(columns=[FEATURE_COLUMNS[0]])
        with self.assertRaises(ValueError):
            validate_dataset(missing_col_df)

        null_df = df.copy()
        null_df.loc[0, FEATURE_COLUMNS[0]] = np.nan
        with self.assertRaises(ValueError):
            validate_dataset(null_df)

        bad_time_df = df.copy()
        bad_time_df.loc[0, "Recency (months)"] = 10
        bad_time_df.loc[0, "Time (months)"] = 5
        with self.assertRaises(ValueError):
            validate_dataset(bad_time_df)

        bad_target_df = df.copy()
        bad_target_df.loc[0, TARGET_COLUMN] = 2
        with self.assertRaises(ValueError):
            validate_dataset(bad_target_df)

    def test_stratified_split_and_preprocessing_pipeline(self):
        df = load_dataset()
        X, y = prepare_features_and_target(df)
        X_train, X_test, y_train, y_test = split_dataset(X, y)

        self.assertEqual(len(X_train), 598)
        self.assertEqual(len(X_test), 150)
        self.assertAlmostEqual(float(y_train.mean()), float(y.mean()), places=2)
        self.assertAlmostEqual(float(y_test.mean()), float(y.mean()), places=2)

        pipe = build_preprocessing_pipeline()
        X_train_scaled = pipe.fit_transform(X_train)
        X_test_scaled = pipe.transform(X_test)
        self.assertEqual(X_train_scaled.shape, (598, 4))
        self.assertEqual(X_test_scaled.shape, (150, 4))
        self.assertTrue(np.allclose(X_train_scaled.mean(axis=0), 0.0, atol=1e-7))


class TestMLTrainingAndPrediction(unittest.TestCase):
    def test_training_saves_artifacts_and_reports_in_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            artifacts_dir = tmp_path / "model_artifacts"
            reports_dir = tmp_path / "reports"

            metadata = train_and_evaluate(
                artifacts_dir=artifacts_dir,
                reports_dir=reports_dir,
                random_state=42,
            )

            self.assertTrue((artifacts_dir / "best_model.joblib").exists())
            self.assertTrue((artifacts_dir / "preprocessing_pipeline.joblib").exists())
            self.assertTrue((artifacts_dir / "model_metadata.json").exists())
            self.assertTrue((reports_dir / "evaluation_metrics.json").exists())
            self.assertTrue((reports_dir / "confusion_matrices.json").exists())
            self.assertTrue((reports_dir / "cv_results.json").exists())
            self.assertTrue((reports_dir / "reproducibility.json").exists())
            self.assertTrue((reports_dir / "model_comparison_report.md").exists())

            self.assertEqual(metadata["selected_model"]["key"], "logistic_regression_balanced")

            # Reload saved artifact without retraining and predict
            predictor = BloodDonationPredictor(artifacts_dir=artifacts_dir)
            result = predictor.predict(
                recency_months=2,
                frequency_times=6,
                monetary_cc=1500,
                time_months=16,
            )
            self.assertIn(result["predicted_class"], (0, 1))
            self.assertIsNotNone(result["probability_score"])
            self.assertGreaterEqual(result["probability_score"], 0.0)
            self.assertLessEqual(result["probability_score"], 1.0)
            self.assertIn("historical donation", result["disclaimer"].lower())
            self.assertIn("not predict emergency", result["disclaimer"].lower())

    def test_prediction_against_saved_production_artifacts(self):
        result = predict_historical_donation(
            recency_months=2,
            frequency_times=10,
            monetary_cc=2500,
            time_months=28,
        )
        self.assertIn(result["predicted_class"], (0, 1))
        self.assertEqual(result["target_scope"], "UCI_HISTORICAL_DONATION_BEHAVIOR")
        self.assertEqual(result["model_info"]["model_key"], "logistic_regression_balanced")

    def test_missing_model_artifact_raises(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            predictor = BloodDonationPredictor(artifacts_dir=empty_dir)
            with self.assertRaises(ModelArtifactNotFoundError):
                predictor.predict(2, 4, 1000, 12)

    def test_invalid_prediction_inputs_rejected(self):
        invalid_cases = [
            (-1, 4, 1000, 12),          # negative recency
            (2, 0, 1000, 12),           # frequency < 1
            (2, 4, 0, 12),              # monetary <= 0
            (10, 4, 1000, 5),           # time < recency
            (float("nan"), 4, 1000, 12),# NaN
            (2, 4, float("inf"), 12),   # Inf
            (True, 4, 1000, 12),        # bool
            ("abc", 4, 1000, 12),       # non-numeric
            (None, 4, 1000, 12),        # None
        ]
        for recency, freq, mon, time_m in invalid_cases:
            with self.subTest(inputs=(recency, freq, mon, time_m)):
                with self.assertRaises(InvalidPredictionInputError):
                    predict_historical_donation(recency, freq, mon, time_m)


if __name__ == "__main__":
    unittest.main()
