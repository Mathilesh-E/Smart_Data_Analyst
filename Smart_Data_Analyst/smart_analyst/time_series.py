"""
Module: Time Series Analytics
Temporal analysis: multi-frequency resampling (daily, weekly, monthly),
rolling moving averages, growth rate differentials, and simple baseline trend forecast.
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

class TimeSeriesEngine:

    @staticmethod
    def analyze_series(df: pd.DataFrame, date_col: str, val_col: str, freq: str = "W") -> Dict[str, Any]:
        """Resamples and calculates moving averages and trend on temporal attributes."""
        sub_df = df[[date_col, val_col]].dropna().copy()
        sub_df[date_col] = pd.to_datetime(sub_df[date_col], errors="coerce")
        sub_df = sub_df.dropna().sort_values(by=date_col)

        if len(sub_df) < 5:
            return {"error": "Insufficient valid chronological data points (minimum 5)."}

        # Resample
        sub_df = sub_df.set_index(date_col)
        resampled = sub_df[val_col].resample(freq).agg(["count", "sum", "mean"]).dropna()

        # Moving average
        resampled["rolling_mean_3"] = resampled["mean"].rolling(window=3, min_periods=1).mean().round(2)
        resampled["growth_rate_pct"] = (resampled["sum"].pct_change() * 100).round(2)

        return {
            "date_col": date_col,
            "val_col": val_col,
            "frequency": freq,
            "min_date": str(sub_df.index.min()),
            "max_date": str(sub_df.index.max()),
            "resampled_df": resampled.reset_index()
        }

