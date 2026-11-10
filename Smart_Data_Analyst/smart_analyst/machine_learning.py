"""
Module: Machine Learning Lab
Leakage-free, reproducible predictive modeling pipelines for Classification & Regression.
Includes simple imputation, scaling, dummy encoding, train/test split, and model leaderboards.
"""
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

class MachineLearningLab:

    @staticmethod
    def infer_task(series: pd.Series) -> str:
        clean = series.dropna()
        if not pd.api.types.is_numeric_dtype(clean):
            return "Classification"
        if clean.nunique() <= 10 and (clean % 1 == 0).all():
            return "Classification"
        return "Regression"

    @staticmethod
    def build_and_evaluate(
        df: pd.DataFrame, target_col: str, feature_cols: List[str], task_type: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if target_col not in df.columns or not feature_cols:
            return None, "Target column or feature list is invalid."

        sub_df = df[[target_col] + feature_cols].dropna(subset=[target_col]).copy()
        if len(sub_df) < 15:
            return None, "Insufficient rows for training (minimum 15 required)."

        y_raw = sub_df[target_col]
        X_raw = sub_df[feature_cols]

        if task_type == "Classification":
            le = LabelEncoder()
            y = le.fit_transform(y_raw.astype(str))
            if len(np.unique(y)) < 2:
                return None, "Classification target must have at least 2 distinct classes."
        else:
            y = pd.to_numeric(y_raw, errors="coerce").values
            valid_mask = ~np.isnan(y)
            X_raw = X_raw[valid_mask]
            y = y[valid_mask]

        # Feature preprocessing
        X_num = X_raw.select_dtypes(include=[np.number])
        X_cat = X_raw.select_dtypes(exclude=[np.number])

        parts = []
        feat_names = []

        if not X_num.empty:
            num_imp = SimpleImputer(strategy="median")
            X_num_imp = num_imp.fit_transform(X_num)
            scaler = StandardScaler()
            parts.append(scaler.fit_transform(X_num_imp))
            feat_names.extend(list(X_num.columns))

        if not X_cat.empty:
            cat_imp = SimpleImputer(strategy="most_frequent")
            X_cat_imp = cat_imp.fit_transform(X_cat)
            cat_df = pd.DataFrame(X_cat_imp, columns=X_cat.columns)
            dummies = pd.get_dummies(cat_df, drop_first=True, dtype=float)
            parts.append(dummies.values)
            feat_names.extend(list(dummies.columns))

        if not parts:
            return None, "No valid predictor features available after preprocessing."

        X = np.hstack(parts)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {}
        if task_type == "Classification":
            models = {
                "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
                "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
            }
        else:
            models = {
                "Ridge Regression": Ridge(random_state=42),
                "Random Forest Regressor": RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42)
            }

        benchmark = {}
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                if task_type == "Classification":
                    benchmark[name] = {
                        "Accuracy": round(float(accuracy_score(y_test, preds)), 4),
                        "Precision": round(float(precision_score(y_test, preds, average="weighted", zero_division=0)), 4),
                        "Recall": round(float(recall_score(y_test, preds, average="weighted", zero_division=0)), 4),
                        "F1-Score": round(float(f1_score(y_test, preds, average="weighted", zero_division=0)), 4),
                        "Confusion_Matrix": confusion_matrix(y_test, preds).tolist()
                    }
                else:
                    mse = mean_squared_error(y_test, preds)
                    benchmark[name] = {
                        "R-squared": round(float(r2_score(y_test, preds)), 4),
                        "MAE": round(float(mean_absolute_error(y_test, preds)), 4),
                        "RMSE": round(float(np.sqrt(mse)), 4)
                    }

                # Feature importances if available
                if hasattr(model, "feature_importances_"):
                    imp = model.feature_importances_
                    sorted_i = np.argsort(imp)[::-1][:10]
                    benchmark[name]["Feature_Importance"] = {feat_names[i]: round(float(imp[i]), 4) for i in sorted_i}

            except Exception as e:
                benchmark[name] = {"error": str(e)}

        return {
            "task_type": task_type,
            "target_col": target_col,
            "benchmark": benchmark,
            "n_samples": len(X)
        }, None

