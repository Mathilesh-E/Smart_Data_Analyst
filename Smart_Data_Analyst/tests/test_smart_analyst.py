"""
Full test suite for Smart Data Analyst:
- Data Loader
- Type Inference
- Profiler
- Quality Engine
- Cleaning Engine
- Statistics Lab
- Clustering Engine
- Anomaly Detector
- Time Series Engine
- Machine Learning Lab
- Reporting Exporter
"""
import pytest
import pandas as pd
import numpy as np

from smart_analyst.data_loader import DataLoader
from smart_analyst.type_inference import TypeInferenceEngine
from smart_analyst.profiler import DataProfiler
from smart_analyst.quality import DataQualityEngine
from smart_analyst.cleaning import DataCleaningEngine
from smart_analyst.statistics import StatisticalLab
from smart_analyst.clustering import ClusteringEngine
from smart_analyst.anomaly_detection import AnomalyDetector
from smart_analyst.time_series import TimeSeriesEngine
from smart_analyst.machine_learning import MachineLearningLab
from smart_analyst.reporting import ReportExporter

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "id": range(1, 101),
        "age": [25, 30, 35, 40, np.nan] * 20,
        "salary": [50000, 60000, 75000, 80000, 250000] * 20,
        "department": ["Sales", "Engineering", "Marketing", "HR", "Sales"] * 20,
        "active": [True, False, True, True, False] * 20,
        "constant_col": ["Fixed"] * 100
    })

def test_loader_csv():
    csv_bytes = "a,b\n1,10\n2,20\n3,30".encode("utf-8")
    df, err = DataLoader.load_dataset(csv_bytes, "test.csv")
    assert err is None
    assert df is not None
    assert df.shape == (3, 2)

def test_loader_empty():
    df, err = DataLoader.load_dataset(b"", "empty.csv")
    assert df is None
    assert "empty" in err.lower()

def test_type_inference(sample_df):
    assert TypeInferenceEngine.infer_column_type(sample_df["active"]) == "Boolean"
    assert "Numeric" in TypeInferenceEngine.infer_column_type(sample_df["salary"])
    assert TypeInferenceEngine.infer_column_type(sample_df["department"]) == "Categorical"

def test_profiler(sample_df):
    prof = DataProfiler.profile_dataset(sample_df)
    assert prof["summary"]["rows"] == 100
    assert prof["summary"]["columns"] == 6
    assert prof["columns"]["age"]["missing_count"] == 20

def test_quality(sample_df):
    qual = DataQualityEngine.audit_quality(sample_df)
    assert 0 <= qual["score"] <= 100
    assert "constant_col" in qual["metrics"]["constant_cols"]
    assert qual["metrics"]["total_missing"] == 20

def test_cleaning_dedup(sample_df):
    dup_df = pd.concat([sample_df, sample_df.iloc[:5]], ignore_index=True)
    clean_df, log = DataCleaningEngine.apply_action(dup_df, "drop_duplicates", {})
    assert len(clean_df) == 100
    assert "5" in log["description"]

def test_cleaning_impute(sample_df):
    clean_df, log = DataCleaningEngine.apply_action(sample_df, "impute_numeric", {"column": "age", "strategy": "median"})
    assert clean_df["age"].isna().sum() == 0
    assert sample_df["age"].isna().sum() == 20 # Original preserved

def test_statistics():
    a = pd.Series(np.random.normal(10, 2, 50))
    b = pd.Series(np.random.normal(15, 2, 50))
    t_res = StatisticalLab.run_two_sample_ttest(a, b)
    assert "p_value" in t_res
    assert t_res["significant_at_05"] == True

def test_clustering(sample_df):
    res = ClusteringEngine.run_kmeans(sample_df, ["id", "salary"], n_clusters=3)
    assert "silhouette_score" in res
    assert len(res["cluster_means"]) == 3

def test_anomaly_detection(sample_df):
    res = AnomalyDetector.detect_anomalies(sample_df, ["id", "salary"], contamination=0.05)
    assert "anomalies_detected" in res
    assert res["anomalies_detected"] > 0

def test_time_series():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame({"Date": dates, "Sales": np.random.randint(100, 500, 30)})
    res = TimeSeriesEngine.analyze_series(df, "Date", "Sales", freq="W")
    assert "resampled_df" in res
    assert len(res["resampled_df"]) > 0

def test_machine_learning_classification(sample_df):
    res, err = MachineLearningLab.build_and_evaluate(sample_df, "department", ["age", "salary"], "Classification")
    assert err is None
    assert "Random Forest" in res["benchmark"]

def test_machine_learning_regression(sample_df):
    res, err = MachineLearningLab.build_and_evaluate(sample_df, "salary", ["age", "id"], "Regression")
    assert err is None
    assert "Ridge Regression" in res["benchmark"]

def test_report_pdf(sample_df):
    qual = DataQualityEngine.audit_quality(sample_df)
    prof = DataProfiler.profile_dataset(sample_df)
    pdf = ReportExporter.generate_pdf("test.csv", sample_df, qual, prof, [{"title": "Observation", "description": "Test"}])
    assert len(pdf) > 0
    assert pdf.startswith(b"%PDF")

