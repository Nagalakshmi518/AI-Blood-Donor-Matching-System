# Research Report: Historical Blood Donation Behavior Prediction Using RFMT Features

**Project:** AI-Based Real-Time Blood Donor Matching and Response Optimization System (BloodNeed)  
**Module:** `ml/` (Standalone Academic Research & Evaluation Module)  
**Dataset:** UCI Blood Transfusion Service Center (`ml/transfusion.data`)  

---

> **Critical Scope & Safety Statement:**  
> The machine learning models evaluated in this report predict **historical blood donation behavior** (`whether he/she donated blood in March 2007`) from the UCI Blood Transfusion Service Center dataset. This dataset does **not** contain emergency blood request acceptance labels, notification response times, real-time donor availability, or clinical compatibility variables. Therefore, these models **must not** be claimed to predict emergency request acceptance or real-time donor response, and they do **not** replace BloodNeed's deterministic blood-group compatibility, cooldown, eligibility, distance ranking, timeout escalation, or hospital inventory fallback workflows.

---

## 1. Dataset Description and Source

- **Dataset Name:** Blood Transfusion Service Center Data Set (UCI Machine Learning Repository).
- **Source & Citation:** Prof. I-Cheng Yeh, Department of Information Management, Chung-Hua University, Hsin-Chu City, Taiwan (donated October 3, 2008). Reference: Yeh, I-Cheng, Yang, King-Jang, and Ting, Tao-Ming, *"Knowledge discovery on RFM model using Bernoulli sequence,"* *Expert Systems with Applications*, 2008 (`doi:10.1016/j.eswa.2008.07.018`).
- **Collection Context:** Randomly sampled donor records from the Blood Transfusion Service Center in Hsin-Chu City, Taiwan, where a mobile blood collection bus visits a university approximately every three months.
- **Local File:** `ml/transfusion.data` (original file preserved unmodified; metadata documented in `ml/transfusion.names`).

---

## 2. Dataset Size, Integrity, and Class Distribution

Validation executed via `ml/preprocessing.py`:

- **Total Instances:** `748` donor records (`5` integer columns, `0` missing/null values, `0` non-finite values).
- **Train / Test Split:** Stratified 80% / 20% split (`598` training samples, `150` held-out test samples; `random_state=42`).
- **Class Distribution (Full Dataset, N = 748):**
  - Class `0` (Did not donate in March 2007): `570` (`76.20%`)
  - Class `1` (Donated in March 2007): `178` (`23.80%`)
  - Training split positive rate: `23.75%`; Test split positive rate: `24.00%`
- **Duplicates & Structural Observations:**
  - **Exact Duplicate Rows:** `215` rows share identical `(R, F, M, T, Target)` values across `502` unique `(R, F, M, T)` feature combinations. These rows are retained because each row in the UCI sample represents a distinct randomly sampled donor; removing identical feature vectors would artificially distort the empirical class prior (`23.80%`).
  - **Conflicting-Target Feature Vectors:** `31` unique `(R, F, M, T)` combinations appear with both `0` and `1` targets, imposing an inherent Bayes-error ceiling on classification accuracy using only RFMT features.
  - **Exact Linear Collinearity:** `Monetary (c.c. blood) = 250 × Frequency (times)` holds for all `748` rows (`100%`).
  - **Temporal Consistency:** `Time (months) >= Recency (months)` holds for all `748` rows.

---

## 3. Feature Descriptions

| Feature Column | Type | Min | Max | Mean ± Std | Median | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `Recency (months)` | `int64` | 0 | 74 | 9.5067 ± 8.0954 | 7.0 | Months since the donor's last blood donation |
| `Frequency (times)` | `int64` | 1 | 50 | 5.5147 ± 5.8393 | 4.0 | Total number of donations made by the donor |
| `Monetary (c.c. blood)` | `int64` | 250 | 12500 | 1378.6765 ± 1459.8268 | 1000.0 | Total blood donated in cubic centimeters (`250 × Frequency`) |
| `Time (months)` | `int64` | 2 | 98 | 34.2821 ± 24.3767 | 28.0 | Months since the donor's first blood donation |
| `whether he/she donated blood in March 2007` *(Target)* | `int64` | 0 | 1 | 0.2380 ± 0.4261 | 0.0 | Binary historical donation indicator (`1` = yes, `0` = no) |

---

## 4. Data Preprocessing Methods

Implemented in `ml/preprocessing.py` with strict leakage prevention:

1. **Schema & Domain Validation:** Verifies exact column names, numeric dtypes, finiteness, non-negative `Recency` and `Time`, `Frequency >= 1`, `Monetary > 0`, `Time >= Recency`, and binary target `{0, 1}`.
2. **Leakage-Safe Splitting:** Stratified train/test split (`test_size=0.2`, `random_state=42`) performed *before* fitting any imputer, scaler, or classifier.
3. **Scikit-Learn Preprocessing Pipeline:**
   - `SimpleImputer(strategy="median")` — defensive median imputation for inference robustness (0 nulls in training data).
   - `StandardScaler()` — zero-mean, unit-variance standardization fitted exclusively inside each training fold during cross-validation and on `X_train` before final evaluation.

---

## 5. Models Used and Experimental Methodology

### 5.1 Candidate Models
1. **Logistic Regression (Baseline):** L2-regularized linear classifier (`max_iter=1000`, `random_state=42`) with default class weights.
2. **Logistic Regression (Class-Balanced):** L2-regularized linear classifier with `class_weight="balanced"` to counter the 76.2% / 23.8% class imbalance.
3. **Random Forest Classifier (Comparison):** Non-linear ensemble (`n_estimators=200`, `max_depth=6`, `min_samples_leaf=5`, `random_state=42`) constrained in depth and leaf size to reduce overfitting on `N = 598` training samples.
4. **Random Forest Classifier (Class-Balanced):** Same regularized ensemble with `class_weight="balanced_subsample"`.

### 5.2 Validation & Evaluation Methodology
- **Cross-Validation:** `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` executed strictly on the `598`-sample training split, wrapping the full preprocessing + estimator `Pipeline` so scaling parameters are recomputed per fold without data leakage.
- **Held-Out Evaluation:** Models are fitted on the full `598`-sample training split and evaluated once on the untouched `150`-sample stratified test split.
- **Imbalance-Aware Selection Criterion:** Because a trivial majority-class predictor achieves `76.20%` accuracy while missing 100% of donors (`Recall = 0`, `F1 = 0`), models are compared and selected using **Stratified CV F1-score** and **ROC-AUC** rather than accuracy alone.

---

## 6. Actual Experimental Results

### 6.1 Stratified 5-Fold Cross-Validation Results (Training Split, N = 598)

| Model | Accuracy (Mean ± Std) | Precision (Mean ± Std) | Recall (Mean ± Std) | F1-Score (Mean ± Std) | ROC-AUC (Mean ± Std) |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression (Baseline) | 0.7726 ± 0.0183 | 0.6224 ± 0.1687 | 0.1200 ± 0.0328 | 0.2002 ± 0.0529 | 0.7391 ± 0.0407 |
| **Logistic Regression (Class-Balanced)** | 0.6472 ± 0.0713 | 0.3833 ± 0.0615 | **0.7470 ± 0.0726** | **0.5047 ± 0.0618** | **0.7400 ± 0.0402** |
| Random Forest Classifier (Comparison) | 0.7775 ± 0.0148 | 0.5823 ± 0.1143 | 0.2603 ± 0.0379 | 0.3565 ± 0.0399 | 0.7155 ± 0.0376 |
| Random Forest Classifier (Class-Balanced) | 0.7224 ± 0.0422 | 0.4426 ± 0.0594 | 0.5495 ± 0.1171 | 0.4823 ± 0.0494 | 0.7151 ± 0.0336 |

### 6.2 Held-Out Stratified Test Set Results (N = 150; 114 Negative, 36 Positive)

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Confusion Matrix `[[TN, FP], [FN, TP]]` |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression (Baseline) | 0.7667 | 0.5714 | 0.1111 | 0.1860 | 0.7878 | `[[111, 3], [32, 4]]` |
| **Logistic Regression (Class-Balanced)** | 0.7200 | 0.4545 | **0.8333** | **0.5882** | 0.7848 | `[[78, 36], [6, 30]]` |
| Random Forest Classifier (Comparison) | 0.7933 | 0.5926 | 0.4444 | 0.5079 | 0.7766 | `[[103, 11], [20, 16]]` |
| Random Forest Classifier (Class-Balanced) | 0.7333 | 0.4643 | 0.7222 | 0.5652 | 0.7695 | `[[84, 30], [10, 26]]` |

---

## 7. Model Comparison and Selection Rationale

- **Why Default-Weight Models Fail the Imbalanced Objective:**  
  Although `Random Forest Classifier (Comparison)` achieved the highest raw test accuracy (`0.7933`) and `Logistic Regression (Baseline)` achieved `0.7667`, both models heavily favored the majority class (`0`). The baseline Logistic Regression missed `32` out of `36` actual donors (`Recall = 0.1111`, `F1 = 0.1860`), and the default Random Forest missed `20` out of `36` donors (`Recall = 0.4444`, `F1 = 0.5079`).
- **Why Logistic Regression (Class-Balanced) Is Selected:**  
  1. **Highest Stratified CV F1-Score (`0.5047`) and CV ROC-AUC (`0.7400`)** across all four candidates.
  2. **Highest Held-Out Test F1-Score (`0.5882`) and Minority Recall (`0.8333`)**, correctly identifying `30` of `36` donors while maintaining `0.7848` ROC-AUC.
  3. **Simplicity and Generalization:** With only 3 independent degrees of freedom (`Monetary` is `250 × Frequency`) and `598` training samples, linear decision boundaries generalize slightly better than tree ensembles (`0.7848` vs. `0.7695`–`0.7766` test ROC-AUC) and yield interpretable coefficients.

---

## 8. Limitations & Operational Gap Analysis

1. **Target Mismatch (Historical vs. Real-Time Emergency):** The UCI target records whether a donor gave blood at a scheduled university blood bus in March 2007. It does **not** measure whether a donor will accept an urgent hospital notification, respond within 15–30 minutes, or be medically eligible/available today.
2. **Database Schema Gap in BloodNeed:** Inspecting `app/models/donor.py` and `app/models/donation.py` confirms that BloodNeed's operational schema tracks `last_donation_date`, `total_donations`, `reliability_score`, `availability`, and `next_eligible_date`, but does **not** store `Time (months)` since the donor's very first lifetime donation (`first_donation_date`), lifetime `Monetary (c.c. blood)`, or pre-platform donation history (new donors start at `total_donations = 0`, whereas UCI requires `Frequency >= 1`). Consequently, live donor records are **not** artificially coerced into the UCI model.
3. **Small Sample Size & Feature Redundancy:** `N = 748` records from a single city/university collection setting limits external clinical generalizability, and `31` conflicting-label RFMT combinations prevent deterministic separation using RFMT features alone.
4. **Future Operational ML Data Requirements:** To train a true emergency-response predictor inside BloodNeed, the platform would need to log historical `DonorMatch` / `ResponseHistory` outcomes (`Accepted` vs. `Rejected`/`Missed`), `response_time_seconds`, `distance_km`, `emergency_level`, `time_of_day`, `days_since_last_donation`, and `donor_acceptance_rate` across sufficient real-world requests.

---

## 9. Reproducibility Details

- **Random Seed:** `42` (applied to `train_test_split`, `StratifiedKFold`, `LogisticRegression`, and `RandomForestClassifier`).
- **Environment Recorded in `ml/reports/reproducibility.json`:**
  - Python `3.11.9`
  - `scikit-learn == 1.9.0`
  - `pandas == 2.1.4`
  - `numpy == 1.26.4`
  - `joblib == 1.6.0`
- **Saved Artifacts (`ml/model_artifacts/` & `ml/reports/`):**
  - `ml/model_artifacts/best_model.joblib` (full fitted preprocessing + classifier `Pipeline`)
  - `ml/model_artifacts/preprocessing_pipeline.joblib` (fitted `SimpleImputer` + `StandardScaler`)
  - `ml/model_artifacts/model_metadata.json`
  - `ml/reports/evaluation_metrics.json`, `confusion_matrices.json`, `cv_results.json`, `reproducibility.json`, `model_comparison_report.md`, `research_report.md`
