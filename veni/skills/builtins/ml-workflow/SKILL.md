---
name: "ML Workflow"
description: "Train/val/test discipline, data leakage prevention, reproducibility, model evaluation"
triggers: ["model", "train", "sklearn", "pytorch", "tensorflow", "accuracy", "loss", "dataset", "feature", "overfitting", "cross-validation", "ml", "machine learning"]
version: "1.0.0"
author: "veni-team"
---

# ML Workflow Skill

## Data Splits — Non-Negotiable Rules
- Split *before* any preprocessing — fit scalers/encoders on train only, transform val/test
- Flag immediately: fitting a scaler on the full dataset before splitting = data leakage
- Stratify classification splits: `train_test_split(..., stratify=y)`
- Time-series data: split by time, never randomly

## Data Leakage — Flag These Patterns
```python
# WRONG — scaler sees test data
scaler = StandardScaler().fit(X)
X_train, X_test = train_test_split(scaler.transform(X), ...)

# RIGHT
X_train, X_test, y_train, y_test = train_test_split(X, y, ...)
scaler = StandardScaler().fit(X_train)
X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)
```
Also flag: target encoding computed on full dataset, features derived from the target.

## Evaluation
- Never report only accuracy on imbalanced classes — require precision/recall/F1
- Report confidence intervals, not point estimates: `cross_val_score` mean ± std
- Baseline first: what does a majority-class or mean predictor score?
- Flag: evaluating on training data and calling it "model performance"

## Reproducibility
```python
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)  # if PyTorch
# Pass random_state=SEED to every sklearn estimator
```

## Model Selection
- Use `cross_val_score` for model comparison, not a single train/test split
- Hyperparameter search: use val set or CV — never tune on test set
- Flag: choosing the model with best test score = test set leakage

## Common Mistakes to Flag
- `model.fit(X_test, y_test)` — fitting on test data
- Dropping NaN rows after splitting (different sizes break pipelines)
- Using `accuracy_score` on imbalanced data without checking class distribution
- Reporting R² without also reporting residual plots
