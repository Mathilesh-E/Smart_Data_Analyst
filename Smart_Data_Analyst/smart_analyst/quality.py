"""
Module: Data Quality
Audit engine detecting missingness, duplicate rows, zero-variance/constant columns,
empty columns, infinite values, and calculating the explainable Data Quality Index.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Heuristic weights for Data Quality Score:
# Q = 100 - (0.50 * M + 0.25 * D + 0.15 * C + 0.10 * I)
WEIGHT_M = 0.50
WEIGHT_D = 0.25
WEIGHT_C = 0.15
WEIGHT_I = 0.10

class DataQualityEngine:

    @staticmethod
    def audit_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """Performs full statistical data quality audit."""
        n_rows, n_cols = df.shape
        if n_rows == 0 or n_cols == 0:
            return {
                "score": 0.0,
                "status": "Critical",
                "status_color": "#ef4444",
                "metrics": {},
                "deductions": {},
                "issues": [{"title": "Empty Dataset", "severity": "Critical", "description": "0 rows or 0 columns detected."}]
            }

        total_cells = n_rows * n_cols
        total_missing = int(df.isna().sum().sum())
        missing_pct = (total_missing / total_cells) * 100

        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = (duplicate_rows / n_rows) * 100

        constant_cols = []
        near_constant_cols = []
        empty_cols = []

        for col in df.columns:
            s = df[col].dropna()
            if len(s) == 0:
                empty_cols.append(col)
            elif s.nunique() == 1:
                constant_cols.append(col)
            elif len(s) > 10 and (s.value_counts(normalize=True).iloc[0] > 0.98):
                near_constant_cols.append(col)

        constant_pct = (len(constant_cols) / n_cols) * 100

        # Outliers & Invalid Values
        infinite_values = 0
        total_outliers = 0
        outlier_info = {}

        for col in df.select_dtypes(include=[np.number]).columns:
            s = df[col].dropna()
            inf_count = int(np.isinf(s).sum())
            infinite_values += inf_count

            if len(s) >= 4:
                finite_s = s[~np.isinf(s)]
                q1 = float(finite_s.quantile(0.25))
                q3 = float(finite_s.quantile(0.75))
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = int(((finite_s < lower) | (finite_s > upper)).sum())
                if outliers > 0:
                    outlier_info[col] = {
                        "count": outliers,
                        "lower_bound": round(lower, 2),
                        "upper_bound": round(upper, 2),
                        "pct": round((outliers / len(s)) * 100, 2)
                    }
                    total_outliers += outliers

        # Invalid percentage: infinite values + cells in 100% empty columns
        invalid_cells = infinite_values + (len(empty_cols) * n_rows)
        invalid_pct = (invalid_cells / total_cells) * 100

        # Score calculation
        deduction_m = min(100.0, missing_pct) * WEIGHT_M
        deduction_d = min(100.0, duplicate_pct) * WEIGHT_D
        deduction_c = min(100.0, constant_pct) * WEIGHT_C
        deduction_i = min(100.0, invalid_pct) * WEIGHT_I

        total_deduction = deduction_m + deduction_d + deduction_c + deduction_i
        raw_score = 100.0 - total_deduction
        quality_score = max(0.0, min(100.0, round(raw_score, 1)))

        if quality_score >= 85:
            status = "Excellent"
            status_color = "#10b981"
        elif quality_score >= 70:
            status = "Good"
            status_color = "#3b82f6"
        elif quality_score >= 50:
            status = "Moderate"
            status_color = "#f59e0b"
        else:
            status = "Critical"
            status_color = "#ef4444"

        # Catalog diagnostic issues
        issues = []
        if total_missing > 0:
            issues.append({
                "title": f"{total_missing:,} Missing Values ({missing_pct:.1f}%)",
                "severity": "danger" if missing_pct > 15 else "warning",
                "description": f"Missing cells detected across {len([c for c in df.columns if df[c].isna().sum() > 0])} columns."
            })
        if duplicate_rows > 0:
            issues.append({
                "title": f"{duplicate_rows:,} Duplicate Rows Detected",
                "severity": "danger" if duplicate_pct > 10 else "warning",
                "description": f"{duplicate_pct:.2f}% of rows are exact duplicate records."
            })
        if constant_cols:
            issues.append({
                "title": f"{len(constant_cols)} Constant Columns (Zero Variance)",
                "severity": "warning",
                "description": f"Columns [{', '.join(constant_cols)}] contain only a single value across all rows."
            })
        if empty_cols:
            issues.append({
                "title": f"{len(empty_cols)} Completely Empty Columns",
                "severity": "danger",
                "description": f"Columns [{', '.join(empty_cols)}] contain 100% null values."
            })
        if total_outliers > 0:
            issues.append({
                "title": f"{total_outliers:,} Statistical Outliers (1.5 × IQR)",
                "severity": "warning",
                "description": f"Potential extreme values found across {len(outlier_info)} numeric columns."
            })

        return {
            "score": quality_score,
            "status": status,
            "status_color": status_color,
            "metrics": {
                "missing_pct": round(missing_pct, 2),
                "total_missing": total_missing,
                "duplicate_pct": round(duplicate_pct, 2),
                "duplicate_rows": duplicate_rows,
                "constant_cols": constant_cols,
                "constant_cols_count": len(constant_cols),
                "near_constant_cols": near_constant_cols,
                "empty_cols": empty_cols,
                "total_outliers": total_outliers,
                "outlier_info": outlier_info,
                "infinite_values": infinite_values,
                "completeness_pct": round(100.0 - missing_pct, 2)
            },
            "deductions": {
                "missing": round(deduction_m, 2),
                "duplicates": round(deduction_d, 2),
                "constant": round(deduction_c, 2),
                "invalid": round(deduction_i, 2),
                "total": round(total_deduction, 2)
            },
            "issues": issues
        }

