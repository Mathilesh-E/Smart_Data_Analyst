"""
Module: Type Inference
Heuristic, explainable type inference engine across tabular attributes:
Numeric (Integer/Float), Categorical, Boolean, DateTime, Text, Identifier, Empty.
"""
import re
from typing import Dict, Any, List
import pandas as pd
import numpy as np

class TypeInferenceEngine:

    @staticmethod
    def infer_column_type(series: pd.Series) -> str:
        """
        Dynamically infers semantic data type without hardcoded column names.
        """
        clean = series.dropna()
        n_rows = len(series)
        n_valid = len(clean)

        if n_valid == 0:
            return "Empty"

        # 1. Explicit or implicit Boolean detection
        if pd.api.types.is_bool_dtype(series):
            return "Boolean"
        
        unique_vals = set(clean.unique())
        bool_candidates = {
            True, False, 0, 1, "0", "1", "true", "false", "True", "False",
            "yes", "no", "Yes", "No", "Y", "N", "y", "n"
        }
        if unique_vals.issubset(bool_candidates) and len(unique_vals) <= 2:
            return "Boolean"

        # 2. DateTime detection
        if pd.api.types.is_datetime64_any_dtype(series):
            return "DateTime"

        # Check date-like string objects
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            sample = clean.head(50).astype(str)
            # Heuristic pattern for date separators
            if sample.str.contains(r'[-/:]').mean() > 0.8:
                try:
                    pd.to_datetime(sample, errors="raise")
                    return "DateTime"
                except Exception:
                    pass

        # 3. Numeric detection (including numeric values stored as strings)
        if pd.api.types.is_numeric_dtype(series):
            n_unique = clean.nunique()
            # Identifier check: strictly unique sequential integers
            if n_unique == n_rows and n_rows >= 20:
                # If strictly sequential
                sorted_vals = clean.sort_values().values
                if np.array_equal(sorted_vals, np.arange(sorted_vals[0], sorted_vals[0] + len(sorted_vals))):
                    return "Identifier"
            if pd.api.types.is_integer_dtype(series):
                return "Numeric (Integer)"
            return "Numeric (Float)"

        # String numeric coercion test
        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            converted = pd.to_numeric(clean.head(100), errors="coerce")
            if converted.notna().mean() > 0.95:
                # String numeric
                return "Numeric (Float)"

        # 4. Text vs Identifier vs Categorical
        n_unique = clean.nunique()
        ratio_unique = n_unique / max(n_valid, 1)

        # High uniqueness on strings with decent volume -> Identifier
        if ratio_unique > 0.92 and n_valid >= 30:
            return "Identifier"

        # Average string length check
        avg_len = clean.astype(str).str.len().mean()
        if avg_len > 60 or n_unique > 800:
            return "Text"

        return "Categorical"

