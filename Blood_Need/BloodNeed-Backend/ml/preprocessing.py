"""Data loading, validation, splitting, and preprocessing for UCI Blood Transfusion dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ML_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = ML_DIR / "transfusion.data"

FEATURE_COLUMNS = [
    "Recency (months)",
    "Frequency (times)",
    "Monetary (c.c. blood)",
    "Time (months)",
]

CANONICAL_FEATURE_NAMES = [
    "recency_months",
    "frequency_times",
    "monetary_cc",
    "time_months",
]

TARGET_COLUMN = "whether he/she donated blood in March 2007"

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5


def load_dataset(data_path: str | Path | None = None) -> pd.DataFrame:
    """Load the UCI Blood Transfusion dataset from disk without modifying it."""
    resolved_path = Path(data_path) if data_path is not None else DEFAULT_DATASET_PATH
    if not resolved_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {resolved_path}")

    df = pd.read_csv(resolved_path)
    df.columns = [str(col).strip() for col in df.columns]
    return df


def validate_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate schema, types, missing values, domain bounds, and class distribution."""
    if df is None or df.empty:
        raise ValueError("Dataset is empty.")

    expected_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    extra_columns = [col for col in df.columns if col not in expected_columns]
    if extra_columns:
        raise ValueError(f"Unexpected columns present: {extra_columns}")

    # Verify numeric types and absence of nulls or infinite values
    null_counts = {col: int(df[col].isna().sum()) for col in expected_columns}
    if any(count > 0 for count in null_counts.values()):
        raise ValueError(f"Dataset contains missing values: {null_counts}")

    for col in expected_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' must be numeric, found {df[col].dtype}.")
        values = df[col].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Column '{col}' contains non-finite values.")

    # Domain validity checks
    if (df["Recency (months)"] < 0).any():
        raise ValueError("Recency (months) contains negative values.")
    if (df["Frequency (times)"] < 1).any():
        raise ValueError("Frequency (times) must be >= 1.")
    if (df["Monetary (c.c. blood)"] <= 0).any():
        raise ValueError("Monetary (c.c. blood) must be > 0.")
    if (df["Time (months)"] < 0).any():
        raise ValueError("Time (months) contains negative values.")
    if (df["Time (months)"] < df["Recency (months)"]).any():
        raise ValueError("Invalid records found where Time (months) < Recency (months).")

    unique_targets = set(df[TARGET_COLUMN].unique().tolist())
    if not unique_targets.issubset({0, 1}):
        raise ValueError(f"Target column must be binary {{0, 1}}, found {sorted(unique_targets)}.")

    duplicate_rows = int(df.duplicated().sum())
    unique_feature_combos = int(df[FEATURE_COLUMNS].drop_duplicates().shape[0])
    conflicting_combos = int(
        (df.groupby(FEATURE_COLUMNS)[TARGET_COLUMN].nunique() > 1).sum()
    )
    monetary_exact_multiple = bool(
        (df["Monetary (c.c. blood)"] == 250 * df["Frequency (times)"]).all()
    )

    target_counts = df[TARGET_COLUMN].value_counts().sort_index()
    total_rows = int(len(df))
    class_0 = int(target_counts.get(0, 0))
    class_1 = int(target_counts.get(1, 0))

    feature_summary: Dict[str, Dict[str, float]] = {}
    for col in FEATURE_COLUMNS:
        series = df[col]
        feature_summary[col] = {
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": round(float(series.mean()), 4),
            "std": round(float(series.std(ddof=1)), 4),
            "median": float(series.median()),
        }

    return {
        "row_count": total_rows,
        "feature_count": len(FEATURE_COLUMNS),
        "columns": expected_columns,
        "dtypes": {col: str(df[col].dtype) for col in expected_columns},
        "missing_values": null_counts,
        "duplicate_rows_retained": duplicate_rows,
        "duplicate_note": (
            "Exact duplicate RFMT rows are retained because each row in the UCI sample "
            "represents an independent donor record; dropping them would distort class priors."
        ),
        "unique_feature_combinations": unique_feature_combos,
        "conflicting_target_feature_combinations": conflicting_combos,
        "monetary_equals_250_times_frequency": monetary_exact_multiple,
        "class_distribution": {
            "0_not_donated": class_0,
            "1_donated": class_1,
            "positive_rate": round(class_1 / total_rows, 4),
            "negative_rate": round(class_0 / total_rows, 4),
        },
        "feature_summary": feature_summary,
    }


def prepare_features_and_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract feature matrix X and binary target vector y without mutating df."""
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].astype(int).copy()
    return X, y


def split_dataset(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Perform a stratified train/test split to preserve target class proportions."""
    return train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=random_state,
    )


def build_preprocessing_pipeline() -> Pipeline:
    """Create an unfitted preprocessing pipeline safe against data leakage."""
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
