"""
Module: Cleaning
Non-destructive, user-approved data cleaning engine.
Supports median/mean/mode imputation, outlier capping (Winsorization),
duplicate pruning, whitespace normalization, and full operation rollback.
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

class DataCleaningEngine:

    @staticmethod
    def get_recommendations(df: pd.DataFrame, quality_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates prioritized cleaning recommendations."""
        recs = []
        metrics = quality_report.get("metrics", {})

        # 1. Duplicate rows
        if metrics.get("duplicate_rows", 0) > 0:
            recs.append({
                "id": "drop_duplicates",
                "category": "Duplicates",
                "title": "Remove Duplicate Records",
                "action": "drop_duplicates",
                "issue": f"{metrics['duplicate_rows']} duplicate rows ({metrics['duplicate_pct']}%) detected.",
                "recommendation": "Drop exact duplicate rows to prevent artificial weighting in models and stats.",
                "params": {}
            })

        # 2. Empty columns
        for col in metrics.get("empty_cols", []):
            recs.append({
                "id": f"drop_empty_{col}",
                "category": "Empty",
                "title": f"Drop 100% Empty Column '{col}'",
                "action": "drop_column",
                "issue": "Column contains 0 non-null values.",
                "recommendation": "Remove uninformative empty column.",
                "params": {"column": col}
            })

        # 3. Constant columns
        for col in metrics.get("constant_cols", []):
            recs.append({
                "id": f"drop_const_{col}",
                "category": "Zero Variance",
                "title": f"Drop Constant Column '{col}'",
                "action": "drop_column",
                "issue": "Column has 0 variance (only 1 unique value across all rows).",
                "recommendation": "Drop column as it offers zero predictive or analytic variability.",
                "params": {"column": col}
            })

        # 4. Missing numeric / categorical
        for col in df.columns:
            n_miss = int(df[col].isna().sum())
            if 0 < n_miss < len(df):
                pct = round((n_miss / len(df)) * 100, 1)
                if pd.api.types.is_numeric_dtype(df[col]):
                    recs.append({
                        "id": f"impute_num_{col}",
                        "category": "Missing Values",
                        "title": f"Impute Numeric Missing in '{col}'",
                        "action": "impute_numeric",
                        "issue": f"{n_miss} missing cells ({pct}%).",
                        "recommendation": "Impute with median (robust against outliers) or mean.",
                        "params": {"column": col, "strategy": "median"}
                    })
                else:
                    recs.append({
                        "id": f"impute_cat_{col}",
                        "category": "Missing Values",
                        "title": f"Impute Missing Categories in '{col}'",
                        "action": "impute_categorical",
                        "issue": f"{n_miss} missing cells ({pct}%).",
                        "recommendation": "Impute with mode (most frequent) or fill with 'Unknown'.",
                        "params": {"column": col, "strategy": "Unknown"}
                    })

        # 5. Outlier capping
        for col, info in metrics.get("outlier_info", {}).items():
            if info["count"] > 0:
                recs.append({
                    "id": f"cap_outliers_{col}",
                    "category": "Outliers",
                    "title": f"Cap Outliers in '{col}' (IQR Winsorization)",
                    "action": "cap_outliers",
                    "issue": f"{info['count']} values outside 1.5*IQR bounds [{info['lower_bound']}, {info['upper_bound']}].",
                    "recommendation": "Cap extreme values to IQR fences without deleting legitimate records.",
                    "params": {"column": col, "lower": info["lower_bound"], "upper": info["upper_bound"]}
                })

        return recs

    @staticmethod
    def apply_action(df: pd.DataFrame, action: str, params: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Applies a single cleaning transformation to a copy of dataframe."""
        clean_df = df.copy()
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": action,
            "column": params.get("column", "All Columns"),
            "description": ""
        }

        if action == "drop_duplicates":
            before = len(clean_df)
            clean_df = clean_df.drop_duplicates()
            diff = before - len(clean_df)
            log_entry["description"] = f"Removed {diff} duplicate rows."

        elif action == "drop_column":
            col = params["column"]
            if col in clean_df.columns:
                clean_df = clean_df.drop(columns=[col])
                log_entry["description"] = f"Dropped column '{col}'."

        elif action == "impute_numeric":
            col = params["column"]
            strategy = params.get("strategy", "median")
            if col in clean_df.columns:
                n_miss = int(clean_df[col].isna().sum())
                val = clean_df[col].median() if strategy == "median" else clean_df[col].mean()
                clean_df[col] = clean_df[col].fillna(val)
                log_entry["description"] = f"Imputed {n_miss} missing values in '{col}' with {strategy} ({round(float(val), 2)})."

        elif action == "impute_categorical":
            col = params["column"]
            strategy = params.get("strategy", "Unknown")
            if col in clean_df.columns:
                n_miss = int(clean_df[col].isna().sum())
                if strategy == "mode":
                    mode_val = clean_df[col].mode()
                    val = mode_val.iloc[0] if len(mode_val) > 0 else "Unknown"
                else:
                    val = strategy
                clean_df[col] = clean_df[col].fillna(val)
                log_entry["description"] = f"Imputed {n_miss} missing values in '{col}' with '{val}'."

        elif action == "cap_outliers":
            col = params["column"]
            lower, upper = params["lower"], params["upper"]
            if col in clean_df.columns:
                n_out = int(((clean_df[col] < lower) | (clean_df[col] > upper)).sum())
                clean_df[col] = clean_df[col].clip(lower=lower, upper=upper)
                log_entry["description"] = f"Capped {n_out} outliers in '{col}' to range [{lower}, {upper}]."

        elif action == "whitespace_clean":
            col = params["column"]
            if col in clean_df.columns:
                clean_df[col] = clean_df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
                log_entry["description"] = f"Trimmed whitespace and normalized spaces in '{col}'."

        return clean_df, log_entry

