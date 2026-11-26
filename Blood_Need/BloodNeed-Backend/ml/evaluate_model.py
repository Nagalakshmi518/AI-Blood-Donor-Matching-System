"""Evaluation, cross-validation, model comparison, and selection helpers."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate


def evaluate_classifier(model, X_test, y_test) -> Dict[str, Any]:
    """Compute classification metrics and confusion matrix on a held-out test set."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    roc_auc = None
    if y_proba is not None and len(np.unique(y_test)) > 1:
        roc_auc = round(float(roc_auc_score(y_test, y_proba)), 4)

    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_breakdown": {
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "true_positive": tp,
        },
        "classification_report": classification_report(
            y_test,
            y_pred,
            target_names=["Not Donated (0)", "Donated (1)"],
            output_dict=True,
            zero_division=0,
        ),
    }


def cross_validate_pipeline(
    pipeline,
    X_train,
    y_train,
    n_splits: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Run Stratified K-Fold cross-validation exclusively on the training set."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
    }
    cv_results = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring=scoring,
        return_train_score=False,
    )

    summary: Dict[str, Any] = {"cv_folds": n_splits}
    for metric in scoring:
        scores = cv_results[f"test_{metric}"]
        summary[metric] = {
            "mean": round(float(np.mean(scores)), 4),
            "std": round(float(np.std(scores, ddof=1)), 4),
            "fold_scores": [round(float(s), 4) for s in scores],
        }
    return summary


def select_best_model(model_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the best model using imbalanced-aware criteria rather than accuracy alone.

    Selection priority:
    1. Highest Stratified CV mean F1-score (balances minority-class precision and recall).
    2. Highest Stratified CV mean ROC-AUC (threshold-independent ranking quality).
    3. Highest held-out test F1-score as tie-breaker.
    """
    if not model_records:
        raise ValueError("No candidate models provided for selection.")

    def _ranking_key(record: Dict[str, Any]):
        cv = record["cv_metrics"]
        test = record["test_metrics"]
        return (
            cv["f1"]["mean"],
            cv["roc_auc"]["mean"],
            test["f1_score"],
            test["roc_auc"] or 0.0,
        )

    return max(model_records, key=_ranking_key)
