"""Training script for UCI Blood Transfusion historical donation behavior models."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.evaluate_model import (
    cross_validate_pipeline,
    evaluate_classifier,
    select_best_model,
)
from ml.preprocessing import (
    CV_FOLDS,
    DEFAULT_DATASET_PATH,
    FEATURE_COLUMNS,
    ML_DIR,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    build_preprocessing_pipeline,
    load_dataset,
    prepare_features_and_target,
    split_dataset,
    validate_dataset,
)

ARTIFACTS_DIR = ML_DIR / "model_artifacts"
REPORTS_DIR = ML_DIR / "reports"


def build_candidate_models(random_state: int = RANDOM_STATE) -> List[Dict[str, Any]]:
    """Define baseline and comparison classifiers with shared preprocessing."""
    return [
        {
            "key": "logistic_regression_baseline",
            "name": "Logistic Regression (Baseline)",
            "family": "LogisticRegression",
            "imbalance_strategy": "none (default class weights)",
            "estimator": LogisticRegression(
                random_state=random_state,
                max_iter=1000,
            ),
        },
        {
            "key": "logistic_regression_balanced",
            "name": "Logistic Regression (Class-Balanced)",
            "family": "LogisticRegression",
            "imbalance_strategy": "class_weight='balanced'",
            "estimator": LogisticRegression(
                random_state=random_state,
                max_iter=1000,
                class_weight="balanced",
            ),
        },
        {
            "key": "random_forest_default",
            "name": "Random Forest Classifier (Comparison)",
            "family": "RandomForestClassifier",
            "imbalance_strategy": "none (default class weights)",
            "estimator": RandomForestClassifier(
                n_estimators=200,
                max_depth=6,
                min_samples_leaf=5,
                random_state=random_state,
                n_jobs=1,
            ),
        },
        {
            "key": "random_forest_balanced",
            "name": "Random Forest Classifier (Class-Balanced)",
            "family": "RandomForestClassifier",
            "imbalance_strategy": "class_weight='balanced_subsample'",
            "estimator": RandomForestClassifier(
                n_estimators=200,
                max_depth=6,
                min_samples_leaf=5,
                class_weight="balanced_subsample",
                random_state=random_state,
                n_jobs=1,
            ),
        },
    ]


def _format_comparison_markdown(
    validation_report: Dict[str, Any],
    model_records: List[Dict[str, Any]],
    best_record: Dict[str, Any],
) -> str:
    lines = [
        "# Model Comparison Report — UCI Blood Transfusion Dataset",
        "",
        "> **Scope Notice:** All models below predict historical donation behavior (`March 2007` target in the UCI dataset). They do **not** predict emergency blood request acceptance or real-time donor response.",
        "",
        "## Dataset Summary",
        f"- Rows: `{validation_report['row_count']}` (exact duplicates retained: `{validation_report['duplicate_rows_retained']}`; conflicting-label RFMT combinations: `{validation_report['conflicting_target_feature_combinations']}`)",
        f"- Class Distribution: Not Donated (0) = `{validation_report['class_distribution']['0_not_donated']}` ({validation_report['class_distribution']['negative_rate']*100:.2f}%), Donated (1) = `{validation_report['class_distribution']['1_donated']}` ({validation_report['class_distribution']['positive_rate']*100:.2f}%)",
        "",
        "## Stratified 5-Fold Cross-Validation (Training Split Only)",
        "",
        "| Model | Accuracy (Mean ± Std) | Precision | Recall | F1-Score | ROC-AUC |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for rec in model_records:
        cv = rec["cv_metrics"]
        lines.append(
            f"| {rec['name']} | {cv['accuracy']['mean']:.4f} ± {cv['accuracy']['std']:.4f} "
            f"| {cv['precision']['mean']:.4f} | {cv['recall']['mean']:.4f} "
            f"| {cv['f1']['mean']:.4f} | {cv['roc_auc']['mean']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Held-Out Stratified Test Set (20%)",
            "",
            "| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Confusion Matrix `[[TN, FP], [FN, TP]]` |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for rec in model_records:
        tm = rec["test_metrics"]
        roc_str = f"{tm['roc_auc']:.4f}" if tm["roc_auc"] is not None else "N/A"
        lines.append(
            f"| {rec['name']} | {tm['accuracy']:.4f} | {tm['precision']:.4f} "
            f"| {tm['recall']:.4f} | {tm['f1_score']:.4f} | {roc_str} | `{tm['confusion_matrix']}` |"
        )

    lines.extend(
        [
            "",
            "## Selected Model & Justification",
            f"- **Selected Model:** `{best_record['name']}` (`{best_record['key']}`)",
            "- **Selection Criterion:** Prioritized Stratified 5-Fold CV F1-score and ROC-AUC over raw accuracy because the dataset is imbalanced (76.2% negative vs. 23.8% positive). Default-weight models optimize accuracy by predicting the majority class (`0`) with low minority-class recall, whereas class-balanced models substantially improve recall and F1-score for identifying potential repeat donors.",
        ]
    )
    return "\n".join(lines) + "\n"


def train_and_evaluate(
    data_path: str | Path | None = None,
    artifacts_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
    random_state: int = RANDOM_STATE,
) -> Dict[str, Any]:
    """Run end-to-end validation, training, CV, evaluation, and artifact persistence."""
    resolved_artifacts_dir = Path(artifacts_dir) if artifacts_dir is not None else ARTIFACTS_DIR
    resolved_reports_dir = Path(reports_dir) if reports_dir is not None else REPORTS_DIR
    resolved_artifacts_dir.mkdir(parents=True, exist_ok=True)
    resolved_reports_dir.mkdir(parents=True, exist_ok=True)

    df = load_dataset(data_path)
    validation_report = validate_dataset(df)
    X, y = prepare_features_and_target(df)

    X_train, X_test, y_train, y_test = split_dataset(
        X, y, test_size=TEST_SIZE, random_state=random_state
    )

    model_records: List[Dict[str, Any]] = []
    fitted_pipelines: Dict[str, Pipeline] = {}

    for spec in build_candidate_models(random_state=random_state):
        pipeline = Pipeline(
            steps=[
                ("preprocessing", build_preprocessing_pipeline()),
                ("classifier", spec["estimator"]),
            ]
        )

        cv_metrics = cross_validate_pipeline(
            pipeline,
            X_train,
            y_train,
            n_splits=CV_FOLDS,
            random_state=random_state,
        )

        pipeline.fit(X_train, y_train)
        test_metrics = evaluate_classifier(pipeline, X_test, y_test)

        record = {
            "key": spec["key"],
            "name": spec["name"],
            "family": spec["family"],
            "imbalance_strategy": spec["imbalance_strategy"],
            "cv_metrics": cv_metrics,
            "test_metrics": test_metrics,
        }
        model_records.append(record)
        fitted_pipelines[spec["key"]] = pipeline

    best_record = select_best_model(model_records)
    best_pipeline = fitted_pipelines[best_record["key"]]
    best_preprocessor = best_pipeline.named_steps["preprocessing"]

    # Persist artifacts with relative-safe paths
    best_model_path = resolved_artifacts_dir / "best_model.joblib"
    preprocessor_path = resolved_artifacts_dir / "preprocessing_pipeline.joblib"
    joblib.dump(best_pipeline, best_model_path)
    joblib.dump(best_preprocessor, preprocessor_path)

    for key, pipe in fitted_pipelines.items():
        joblib.dump(pipe, resolved_artifacts_dir / f"{key}.joblib")

    reproducibility = {
        "random_state": random_state,
        "test_size": TEST_SIZE,
        "cv_folds": CV_FOLDS,
        "stratified_split": True,
        "stratified_cv": True,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "train_positive_rate": round(float(y_train.mean()), 4),
        "test_positive_rate": round(float(y_test.mean()), 4),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "package_versions": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    metadata = {
        "dataset": "UCI Blood Transfusion Service Center",
        "dataset_path": "ml/transfusion.data",
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "target_meaning": (
            "Binary indicator of whether the donor donated blood in March 2007 "
            "(historical donation behavior, NOT emergency-response acceptance)."
        ),
        "selected_model": best_record,
        "all_models": model_records,
        "dataset_validation": validation_report,
        "reproducibility": reproducibility,
    }

    # Save structured JSON artifacts
    with open(resolved_artifacts_dir / "model_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    with open(resolved_reports_dir / "evaluation_metrics.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "selected_model_key": best_record["key"],
                "selected_model_name": best_record["name"],
                "models": {
                    rec["key"]: {
                        "name": rec["name"],
                        "cv_metrics": rec["cv_metrics"],
                        "test_metrics": rec["test_metrics"],
                    }
                    for rec in model_records
                },
            },
            f,
            indent=2,
        )

    with open(resolved_reports_dir / "confusion_matrices.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                rec["key"]: {
                    "name": rec["name"],
                    "matrix": rec["test_metrics"]["confusion_matrix"],
                    "breakdown": rec["test_metrics"]["confusion_matrix_breakdown"],
                }
                for rec in model_records
            },
            f,
            indent=2,
        )

    with open(resolved_reports_dir / "cv_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {rec["key"]: rec["cv_metrics"] for rec in model_records},
            f,
            indent=2,
        )

    with open(resolved_reports_dir / "reproducibility.json", "w", encoding="utf-8") as f:
        json.dump(reproducibility, f, indent=2)

    comparison_md = _format_comparison_markdown(validation_report, model_records, best_record)
    with open(resolved_reports_dir / "model_comparison_report.md", "w", encoding="utf-8") as f:
        f.write(comparison_md)

    return metadata


if __name__ == "__main__":
    result = train_and_evaluate()
    selected = result["selected_model"]
    print(f"Training completed. Selected model: {selected['name']}")
    print(
        f"Test Metrics -> Accuracy: {selected['test_metrics']['accuracy']}, "
        f"Precision: {selected['test_metrics']['precision']}, "
        f"Recall: {selected['test_metrics']['recall']}, "
        f"F1: {selected['test_metrics']['f1_score']}, "
        f"ROC-AUC: {selected['test_metrics']['roc_auc']}"
    )
    sys.exit(0)
