"""
Edge case testing for universal robustness:
1. One-column dataset
2. One-row dataset
3. All-numeric dataset
4. All-categorical dataset
5. All-null column
6. High-cardinality categorical column
7. Constant numeric columns
"""
import pytest
import pandas as pd
import numpy as np

from smart_analyst.profiler import DataProfiler
from smart_analyst.quality import DataQualityEngine
from smart_analyst.cleaning import DataCleaningEngine
from smart_analyst.eda import EDAEngine
from smart_analyst.insights import InsightEngine
from smart_analyst.reporting import ReportExporter

def test_one_column_dataset():
    df = pd.DataFrame({"score": [10, 20, 30, 40, 50]})
    prof = DataProfiler.profile_dataset(df)
    assert prof["summary"]["columns"] == 1
    qual = DataQualityEngine.audit_quality(df)
    assert qual["score"] == 100.0
    insights = InsightEngine.generate_insights(df, qual, prof)
    assert len(insights) > 0

def test_one_row_dataset():
    df = pd.DataFrame({"a": [1], "b": ["x"], "c": [3.14]})
    prof = DataProfiler.profile_dataset(df)
    assert prof["summary"]["rows"] == 1
    qual = DataQualityEngine.audit_quality(df)
    assert 0 <= qual["score"] <= 100
    pdf_bytes = ReportExporter.generate_pdf("one_row.csv", df, qual, prof, [], [])
    assert len(pdf_bytes) > 0

def test_all_numeric_dataset():
    df = pd.DataFrame({
        "num1": [1.0, 2.0, 3.0, 4.0],
        "num2": [10.0, 20.0, 30.0, 40.0]
    })
    corr = EDAEngine.calculate_correlations(df)
    assert corr is not None
    assert corr.loc["num1", "num2"] == 1.0

def test_all_categorical_dataset():
    df = pd.DataFrame({
        "cat1": ["A", "B", "C", "A"],
        "cat2": ["High", "Low", "Medium", "High"]
    })
    num_sum = EDAEngine.get_numeric_summary(df)
    assert num_sum.empty
    cat_sum = EDAEngine.get_categorical_summary(df)
    assert len(cat_sum) == 2

def test_all_null_column():
    df = pd.DataFrame({
        "valid": [1, 2, 3, 4],
        "all_null": [np.nan, np.nan, np.nan, np.nan]
    })
    qual = DataQualityEngine.audit_quality(df)
    assert "all_null" in qual["metrics"]["empty_cols"]
    recs = DataCleaningEngine.get_recommendations(df, qual)
    assert any("all_null" in r["title"] or "all_null" in r.get("description", "") for r in recs)
