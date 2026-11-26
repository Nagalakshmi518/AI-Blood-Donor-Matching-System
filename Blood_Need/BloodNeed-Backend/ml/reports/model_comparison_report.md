# Model Comparison Report — UCI Blood Transfusion Dataset

> **Scope Notice:** All models below predict historical donation behavior (`March 2007` target in the UCI dataset). They do **not** predict emergency blood request acceptance or real-time donor response.

## Dataset Summary
- Rows: `748` (exact duplicates retained: `215`; conflicting-label RFMT combinations: `31`)
- Class Distribution: Not Donated (0) = `570` (76.20%), Donated (1) = `178` (23.80%)

## Stratified 5-Fold Cross-Validation (Training Split Only)

| Model | Accuracy (Mean ± Std) | Precision | Recall | F1-Score | ROC-AUC |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression (Baseline) | 0.7726 ± 0.0183 | 0.6224 | 0.1200 | 0.2002 | 0.7391 |
| Logistic Regression (Class-Balanced) | 0.6472 ± 0.0713 | 0.3833 | 0.7470 | 0.5047 | 0.7400 |
| Random Forest Classifier (Comparison) | 0.7775 ± 0.0148 | 0.5823 | 0.2603 | 0.3565 | 0.7155 |
| Random Forest Classifier (Class-Balanced) | 0.7224 ± 0.0422 | 0.4426 | 0.5495 | 0.4823 | 0.7151 |

## Held-Out Stratified Test Set (20%)

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Confusion Matrix `[[TN, FP], [FN, TP]]` |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression (Baseline) | 0.7667 | 0.5714 | 0.1111 | 0.1860 | 0.7878 | `[[111, 3], [32, 4]]` |
| Logistic Regression (Class-Balanced) | 0.7200 | 0.4545 | 0.8333 | 0.5882 | 0.7848 | `[[78, 36], [6, 30]]` |
| Random Forest Classifier (Comparison) | 0.7933 | 0.5926 | 0.4444 | 0.5079 | 0.7766 | `[[103, 11], [20, 16]]` |
| Random Forest Classifier (Class-Balanced) | 0.7333 | 0.4643 | 0.7222 | 0.5652 | 0.7695 | `[[84, 30], [10, 26]]` |

## Selected Model & Justification
- **Selected Model:** `Logistic Regression (Class-Balanced)` (`logistic_regression_balanced`)
- **Selection Criterion:** Prioritized Stratified 5-Fold CV F1-score and ROC-AUC over raw accuracy because the dataset is imbalanced (76.2% negative vs. 23.8% positive). Default-weight models optimize accuracy by predicting the majority class (`0`) with low minority-class recall, whereas class-balanced models substantially improve recall and F1-score for identifying potential repeat donors.
