"""
Module: Statistical Analysis Lab
Scientific hypothesis testing and distribution tests:
Pearson/Spearman, Welch's t-test, Mann-Whitney U, Kruskal-Wallis, Chi-Square, and Shapiro-Wilk.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats

class StatisticalLab:

    @staticmethod
    def run_two_sample_ttest(series_a: pd.Series, series_b: pd.Series) -> Dict[str, Any]:
        """Runs Welch's two-sample t-test (unequal variances assumed)."""
        a = series_a.dropna()
        b = series_b.dropna()
        if len(a) < 3 or len(b) < 3:
            return {"error": "Insufficient sample size (minimum 3 observations per group)."}
        
        stat, pval = stats.ttest_ind(a, b, equal_var=False)
        return {
            "test": "Welch's Two-Sample t-Test",
            "stat_name": "t-statistic",
            "stat_value": round(float(stat), 4),
            "p_value": float(pval),
            "sample_size_a": len(a),
            "sample_size_b": len(b),
            "mean_a": round(float(a.mean()), 3),
            "mean_b": round(float(b.mean()), 3),
            "significant_at_05": pval < 0.05
        }

    @staticmethod
    def run_mann_whitney(series_a: pd.Series, series_b: pd.Series) -> Dict[str, Any]:
        """Runs non-parametric Mann-Whitney U test."""
        a = series_a.dropna()
        b = series_b.dropna()
        if len(a) < 3 or len(b) < 3:
            return {"error": "Insufficient sample size (minimum 3 observations per group)."}
        
        stat, pval = stats.mannwhitneyu(a, b, alternative="two-sided")
        return {
            "test": "Mann-Whitney U Test (Non-parametric)",
            "stat_name": "U-statistic",
            "stat_value": round(float(stat), 4),
            "p_value": float(pval),
            "sample_size_a": len(a),
            "sample_size_b": len(b),
            "median_a": round(float(a.median()), 3),
            "median_b": round(float(b.median()), 3),
            "significant_at_05": pval < 0.05
        }

    @staticmethod
    def run_chi_square(df: pd.DataFrame, cat_col_a: str, cat_col_b: str) -> Dict[str, Any]:
        """Runs Chi-Square test of independence on two categorical variables."""
        contingency = pd.crosstab(df[cat_col_a], df[cat_col_b])
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return {"error": "Contingency table requires at least 2 rows and 2 columns."}

        chi2, pval, dof, expected = stats.chi2_contingency(contingency)
        # Cramér's V effect size
        n = contingency.sum().sum()
        min_dim = min(contingency.shape) - 1
        cramer_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 and n > 0 else 0.0

        return {
            "test": "Chi-Square Test of Independence",
            "stat_name": "Chi2 Statistic",
            "stat_value": round(float(chi2), 4),
            "p_value": float(pval),
            "dof": int(dof),
            "cramers_v": round(float(cramer_v), 3),
            "significant_at_05": pval < 0.05,
            "contingency_table": contingency
        }

