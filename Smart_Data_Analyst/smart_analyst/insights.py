"""
Module: Automated Insights
100% offline, deterministic, statistical observations, anomaly warnings,
and actionable data recommendations derived strictly from computed numbers.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np

class InsightEngine:

    @staticmethod
    def generate_insights(df: pd.DataFrame, quality_report: Dict[str, Any], profile_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []
        n_rows, n_cols = df.shape
        metrics = quality_report.get("metrics", {})

        # 1. Dataset Dimensions
        insights.append({
            "category": "observation",
            "title": "Dataset Volume & Shape",
            "description": f"The dataset encompasses {n_rows:,} records across {n_cols:,} attributes ({n_rows*n_cols:,} total cells).",
            "columns": [],
            "metric": f"{n_rows:,} rows × {n_cols} cols"
        })

        # 2. Duplicate records
        dup_count = metrics.get("duplicate_rows", 0)
        dup_pct = metrics.get("duplicate_pct", 0)
        if dup_count > 0:
            insights.append({
                "category": "warning",
                "title": "Duplicate Rows Present",
                "description": f"{dup_count:,} duplicate rows ({dup_pct:.1f}%) detected. This can artificially bias model weights and aggregations.",
                "columns": [],
                "metric": f"{dup_pct:.1f}% duplicate rate",
                "recommendation": "Execute duplicate pruning in Smart Cleaning."
            })

        # 3. High Missing Data
        missing_pct = metrics.get("missing_pct", 0)
        if missing_pct > 10:
            insights.append({
                "category": "warning",
                "title": "High Overall Missingness",
                "description": f"{missing_pct:.1f}% of all cells are null. Pruning or imputation is required prior to machine learning.",
                "columns": [],
                "metric": f"{missing_pct:.1f}% missing",
                "recommendation": "Review Missing Values tab or apply median/mode imputation."
            })

        # 4. Skewness & Outliers
        for col, col_prof in profile_report.get("columns", {}).items():
            stats = col_prof.get("stats", {})
            skew = stats.get("skewness")
            if skew is not None and abs(skew) > 1.5:
                direction = "right-skewed" if skew > 0 else "left-skewed"
                insights.append({
                    "category": "observation",
                    "title": f"Skewed Distribution in '{col}'",
                    "description": f"Column '{col}' is strongly {direction} (skewness = {skew:.2f}). Consider log or power transforms if fitting linear models.",
                    "columns": [col],
                    "metric": f"Skewness: {skew:.2f}"
                })

            out_pct = stats.get("outlier_pct")
            if out_pct and out_pct > 5:
                insights.append({
                    "category": "observation",
                    "title": f"Concentration of Outliers in '{col}'",
                    "description": f"{stats.get('outlier_count')} data points ({out_pct}%) exceed 1.5*IQR bounds.",
                    "columns": [col],
                    "metric": f"{out_pct}% outliers",
                    "recommendation": "Inspect in Visualization Lab and evaluate IQR Winsorization."
                })

            # High cardinality categorical
            if col_prof.get("type") == "Categorical":
                uniq = col_prof.get("unique_count", 0)
                if uniq > 50:
                    insights.append({
                        "category": "warning",
                        "title": f"High Cardinality in '{col}'",
                        "description": f"Categorical attribute '{col}' contains {uniq} unique categories. One-hot encoding may cause high dimensionality.",
                        "columns": [col],
                        "metric": f"{uniq} distinct categories",
                        "recommendation": "Group rare categories into an 'Other' bucket."
                    })

        # 5. Multicollinearity / High Correlation
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) >= 2:
            corr_mat = df[num_cols].corr()
            cols = list(corr_mat.columns)
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    c1, c2 = cols[i], cols[j]
                    val = corr_mat.loc[c1, c2]
                    if not np.isnan(val) and abs(val) >= 0.75:
                        insights.append({
                            "category": "observation",
                            "title": f"Strong Association: {c1} & {c2}",
                            "description": f"Strong {'positive' if val > 0 else 'negative'} linear correlation observed (r = {val:.2f}). Potential multicollinearity in linear models.",
                            "columns": [c1, c2],
                            "metric": f"r = {val:.2f}"
                        })

        return insights

