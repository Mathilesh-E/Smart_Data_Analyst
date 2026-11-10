"""
Module: EDA Engine
Univariate, bivariate, and multivariate exploratory data analysis:
descriptive summary matrices, skewness, Pearson/Spearman correlations,
and multi-dimensional group aggregations.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class EDAEngine:

    @staticmethod
    def get_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
        """Returns comprehensive descriptive statistics for all numeric features."""
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) == 0:
            return pd.DataFrame()

        summary = df[num_cols].describe().T
        summary["median"] = df[num_cols].median()
        summary["variance"] = df[num_cols].var()
        summary["skewness"] = df[num_cols].skew()
        summary["kurtosis"] = df[num_cols].kurtosis()
        summary["missing"] = df[num_cols].isna().sum()
        summary["zeros"] = (df[num_cols] == 0).sum()

        return summary.round(3)

    @staticmethod
    def get_categorical_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Summarizes top frequencies and proportions for categorical variables."""
        cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns
        results = []
        for col in cat_cols:
            clean = df[col].dropna()
            val_counts = clean.value_counts()
            results.append({
                "column": col,
                "unique_count": clean.nunique(),
                "missing_count": int(df[col].isna().sum()),
                "top_category": str(val_counts.index[0]) if len(val_counts) > 0 else "N/A",
                "top_percentage": round((val_counts.iloc[0] / len(clean)) * 100, 1) if len(val_counts) > 0 else 0.0,
                "distribution": val_counts.head(10).to_dict()
            })
        return results

    @staticmethod
    def calculate_correlations(df: pd.DataFrame, method: str = "pearson") -> Optional[pd.DataFrame]:
        """Calculates pairwise correlation matrix for numeric columns."""
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] < 2:
            return None
        return num_df.corr(method=method).round(3)

    @staticmethod
    def get_top_correlations(corr_df: pd.DataFrame, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Identifies strong pairwise associations from correlation matrix."""
        if corr_df is None or corr_df.empty:
            return []
        pairs = []
        cols = corr_df.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                val = corr_df.loc[c1, c2]
                if not np.isnan(val) and abs(val) >= threshold:
                    pairs.append({
                        "feature_a": c1,
                        "feature_b": c2,
                        "correlation": round(float(val), 3),
                        "direction": "Positive" if val > 0 else "Negative",
                        "strength": "Very Strong" if abs(val) >= 0.8 else "Strong"
                    })
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return pairs

    @staticmethod
    def group_aggregation(df: pd.DataFrame, cat_col: str, num_col: str) -> pd.DataFrame:
        """Groups data by a category and aggregates numeric stats."""
        if cat_col not in df.columns or num_col not in df.columns:
            return pd.DataFrame()
        agg = df.groupby(cat_col)[num_col].agg(["count", "mean", "median", "std", "min", "max"])
        agg.columns = [f"{num_col}_{col}" for col in agg.columns]
        return agg.reset_index().round(2)

