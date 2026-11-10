"""
Module: Profiler
Computes detailed statistical and structural profiles for tabular datasets.
Includes parametric and non-parametric calculations across all inferred types.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from smart_analyst.type_inference import TypeInferenceEngine

class DataProfiler:

    @staticmethod
    def profile_dataset(df: pd.DataFrame, manual_types: Dict[str, str] = None) -> Dict[str, Any]:
        """Generates comprehensive dataset and column-level analytical profiles."""
        manual_types = manual_types or {}
        n_rows, n_cols = df.shape
        total_cells = n_rows * n_cols
        total_missing = int(df.isna().sum().sum())
        missing_pct = round((total_missing / max(total_cells, 1)) * 100, 2)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / max(n_rows, 1)) * 100, 2)
        mem_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        column_profiles = {}
        type_counts = {}

        for col in df.columns:
            series = df[col]
            inferred_type = manual_types.get(col) or TypeInferenceEngine.infer_column_type(series)
            type_counts[inferred_type] = type_counts.get(inferred_type, 0) + 1
            col_profile = DataProfiler.profile_column(series, inferred_type)
            column_profiles[col] = col_profile

        return {
            "summary": {
                "rows": n_rows,
                "columns": n_cols,
                "total_cells": total_cells,
                "total_missing": total_missing,
                "missing_pct": missing_pct,
                "duplicate_rows": duplicate_rows,
                "duplicate_pct": duplicate_pct,
                "memory_mb": mem_mb,
                "type_counts": type_counts,
                "completeness_pct": round(100.0 - missing_pct, 2)
            },
            "columns": column_profiles
        }

    @staticmethod
    def profile_column(series: pd.Series, col_type: str) -> Dict[str, Any]:
        """Calculates column-specific statistics according to data type."""
        n_total = len(series)
        n_missing = int(series.isna().sum())
        missing_pct = round((n_missing / max(n_total, 1)) * 100, 2)
        clean_s = series.dropna()
        n_unique = int(clean_s.nunique())

        profile = {
            "name": series.name,
            "type": col_type,
            "total_count": n_total,
            "missing_count": n_missing,
            "missing_pct": missing_pct,
            "unique_count": n_unique,
            "unique_pct": round((n_unique / max(n_total, 1)) * 100, 2),
            "stats": {}
        }

        # Numeric Statistics
        if ("Numeric" in col_type or pd.api.types.is_numeric_dtype(series)) and col_type != "Boolean":
            if len(clean_s) > 0:
                num_s = pd.to_numeric(clean_s, errors="coerce").dropna().astype(float)
                if len(num_s) > 0:
                    q1 = float(num_s.quantile(0.25))
                    q3 = float(num_s.quantile(0.75))
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers = int(((num_s < lower) | (num_s > upper)).sum())

                    profile["stats"] = {
                        "mean": round(float(num_s.mean()), 3),
                        "std": round(float(num_s.std()), 3) if len(num_s) > 1 else 0.0,
                        "var": round(float(num_s.var()), 3) if len(num_s) > 1 else 0.0,
                        "min": round(float(num_s.min()), 3),
                        "q25": round(q1, 3),
                        "median": round(float(num_s.median()), 3),
                        "q75": round(q3, 3),
                        "max": round(float(num_s.max()), 3),
                        "range": round(float(num_s.max() - num_s.min()), 3),
                        "iqr": round(iqr, 3),
                        "skewness": round(float(num_s.skew()), 3) if len(num_s) > 2 else 0.0,
                        "outlier_count": outliers,
                        "outlier_pct": round((outliers / len(num_s)) * 100, 2),
                        "zeros_count": int((num_s == 0).sum())
                    }

        # Categorical Statistics
        elif col_type in ["Categorical", "Identifier"]:
            if len(clean_s) > 0:
                val_counts = clean_s.value_counts()
                top_cat = str(val_counts.index[0]) if len(val_counts) > 0 else "N/A"
                top_freq = int(val_counts.iloc[0]) if len(val_counts) > 0 else 0
                profile["stats"] = {
                    "top_category": top_cat,
                    "top_frequency": top_freq,
                    "top_percentage": round((top_freq / max(len(clean_s), 1)) * 100, 2),
                    "frequencies": val_counts.head(10).to_dict()
                }

        # Boolean Statistics
        elif col_type == "Boolean":
            if len(clean_s) > 0:
                profile["stats"] = {
                    "distribution": clean_s.astype(str).value_counts().to_dict()
                }

        # DateTime Statistics
        elif col_type == "DateTime":
            try:
                date_s = pd.to_datetime(clean_s, errors="coerce").dropna()
                if len(date_s) > 0:
                    profile["stats"] = {
                        "min_date": str(date_s.min()),
                        "max_date": str(date_s.max()),
                        "days_span": int((date_s.max() - date_s.min()).days)
                    }
            except Exception:
                pass

        # Text Statistics
        elif col_type == "Text":
            if len(clean_s) > 0:
                lens = clean_s.astype(str).str.len()
                profile["stats"] = {
                    "avg_char_length": round(float(lens.mean()), 1),
                    "min_char_length": int(lens.min()),
                    "max_char_length": int(lens.max())
                }

        return profile

