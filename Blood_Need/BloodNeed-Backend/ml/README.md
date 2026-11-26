# BloodNeed Research ML Module (`ml/`)

Standalone, reproducible machine learning module trained on the **UCI Blood Transfusion Service Center** dataset (`ml/transfusion.data`) for academic research and conference paper evaluation.

## Scope & Safety Boundary
- **What this module predicts:** Historical donation tendency (`whether he/she donated blood in March 2007`) from RFMT features (`Recency`, `Frequency`, `Monetary`, `Time`).
- **What this module does NOT predict:** Emergency blood request acceptance, donor response time, real-time availability, or medical compatibility.
- **Operational isolation:** Existing matching, compatibility (`app/ai/compatibility.py`), cooldown/eligibility (`app/matching/services.py`), ranking (`app/ai/ranking.py`), notification, timeout escalation (`app/response/services.py`, `app/matching/timeout.py`), and hospital inventory fallback (`app/hospital/services.py`) workflows remain completely intact and unaffected.

## Folder Structure
- `transfusion.data` / `transfusion.names` — Original UCI dataset and documentation (kept unmodified).
- `preprocessing.py` — Dataset loading, schema/domain validation, stratified 80/20 split, and leakage-safe preprocessing pipeline (`SimpleImputer` + `StandardScaler`).
- `evaluate_model.py` — Stratified K-Fold CV, held-out classification metrics, confusion matrix breakdown, and imbalance-aware model selection.
- `train_model.py` — End-to-end training, comparison (Logistic Regression baseline vs. Random Forest comparison, with and without class balancing), and artifact/report export.
- `predict.py` — Standalone inference & strict input validation with explicit target-scope disclaimer.
- `model_artifacts/` — Saved `.joblib` models, preprocessing pipeline, and `model_metadata.json`.
- `reports/` — Saved evaluation JSONs, comparison table (`model_comparison_report.md`), and publication-ready `research_report.md`.

## Commands (run from `BloodNeed-Backend/`)
```bash
# 1. Train, cross-validate, compare models, and regenerate artifacts/reports
python -m ml.train_model

# 2. Run single-sample inference from CLI
python -m ml.predict --recency 2 --frequency 6 --monetary 1500 --time 16
```
