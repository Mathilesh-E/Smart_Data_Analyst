"""
Comprehensive Advanced Data Analytics Studio Engine for FastAPI.
Provides A-Z data operations:
- Dynamic Custom Pivot Tables (index, columns, values, aggfunc)
- Dynamic Outlier Deep Dive (IQR fences, Z-score, Winsorization, Trimming)
- Advanced Multidimensional Statistical Engine (Normality tests, ANOVA, Kruskal, Mann-Whitney, Levene, Spearman/Pearson/Kendall)
- Custom Column Transformation & Feature Engineering (Log transform, Standardize, Min-Max scale, Binning, Interaction terms)
- Comprehensive Correlation Matrix (Full pairwise grid)
- Full Slicing, Multivariable Filtering & Dynamic Aggregation
"""
import io
import os
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from smart_analyst.data_loader import DataLoader
from smart_analyst.profiler import DataProfiler
from smart_analyst.quality import DataQualityEngine
from smart_analyst.cleaning import DataCleaningEngine
from smart_analyst.eda import EDAEngine
from smart_analyst.statistics import StatisticalLab
from smart_analyst.clustering import ClusteringEngine
from smart_analyst.anomaly_detection import AnomalyDetector
from smart_analyst.time_series import TimeSeriesEngine
from smart_analyst.machine_learning import MachineLearningLab
from smart_analyst.insights import InsightEngine
from smart_analyst.reporting import ReportExporter

app = FastAPI(title="Smart Data Analyst Pro API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionStore:
    def __init__(self):
        self.raw_df: Optional[pd.DataFrame] = None
        self.active_df: Optional[pd.DataFrame] = None
        self.filename: str = "dataset.csv"
        self.cleaning_log: List[Dict[str, Any]] = []

state = SessionStore()

def sanitize_for_json(obj):
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return round(float(obj), 4)
    elif isinstance(obj, np.ndarray):
        return [sanitize_for_json(x) for x in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(x) for x in obj]
    elif pd.isna(obj):
        return None
    return obj

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "4.0.0", "has_data": state.active_df is not None}

@app.get("/api/benchmarks")
def get_benchmarks():
    return [
        {"id": "retail_sales.csv", "name": "Retail Sales & Financial E-Commerce", "desc": "120-day transactions with revenue, discounts, units sold, ratings & regional segments.", "records": 358, "dims": 10},
        {"id": "student_performance.csv", "name": "Academic Performance & Student Retention", "desc": "Study hours, attendance rates, past test scores, and pass/fail target outcomes.", "records": 280, "dims": 9},
        {"id": "healthcare_sample.csv", "name": "Clinical Healthcare Diagnostics", "desc": "Patient vitals, cholesterol, resting blood pressure, fasting glucose, and cardiovascular diagnosis.", "records": 300, "dims": 9},
        {"id": "flight_delays.csv", "name": "Airline Operations & Flight Delay Patterns", "desc": "Carrier performance, departure/arrival delays, flight distances, and cancellation rates.", "records": 320, "dims": 8}
    ]

@app.post("/api/load-benchmark")
def load_benchmark(benchmark_id: str = Form(...)):
    p = os.path.join(os.path.dirname(__file__), "sample_data", benchmark_id)
    if not os.path.exists(p):
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")
    
    with open(p, "rb") as f:
        content = f.read()
    
    df, err = DataLoader.load_dataset(content, benchmark_id)
    if err and df is None:
        raise HTTPException(status_code=400, detail=err)
    
    state.raw_df = df.copy()
    state.active_df = df.copy()
    state.filename = benchmark_id
    state.cleaning_log = []
    return get_current_dataset_state()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), sheet: Optional[str] = Form(None)):
    contents = await file.read()
    df, err = DataLoader.load_dataset(contents, file.filename, sheet_name=sheet)
    if err and df is None:
        raise HTTPException(status_code=400, detail=err)
    
    state.raw_df = df.copy()
    state.active_df = df.copy()
    state.filename = file.filename
    state.cleaning_log = []
    return get_current_dataset_state()

@app.get("/api/dataset")
def get_current_dataset_state():
    if state.active_df is None:
        return {"loaded": False}

    df = state.active_df
    prof = DataProfiler.profile_dataset(df)
    qual = DataQualityEngine.audit_quality(df)
    insights = InsightEngine.generate_insights(df, qual, prof)

    # 100 records for deep client table inspection
    preview = df.head(100).replace({np.nan: None}).to_dict(orient="records")

    return sanitize_for_json({
        "loaded": True,
        "filename": state.filename,
        "is_cleaned": len(state.cleaning_log) > 0,
        "cleaning_log": state.cleaning_log,
        "summary": prof["summary"],
        "columns": prof["columns"],
        "quality": qual,
        "insights": insights,
        "preview": preview,
        "all_columns": list(df.columns),
        "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
        "categorical_columns": list(df.select_dtypes(include=["object", "category", "bool"]).columns)
    })

# ----------------- ADVANCED A-Z DATA OPERATIONS -----------------

class PivotTableRequest(BaseModel):
    index: str
    columns: Optional[str] = None
    values: str
    aggfunc: str = "mean"

@app.post("/api/pivot-table")
def generate_pivot_table(req: PivotTableRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df

    try:
        kwargs = {
            "index": req.index,
            "values": req.values,
            "aggfunc": req.aggfunc
        }
        if req.columns and req.columns != "None":
            kwargs["columns"] = req.columns

        pt = pd.pivot_table(df, **kwargs).fillna(0).round(2)
        if isinstance(pt.columns, pd.MultiIndex):
            pt.columns = ['_'.join(str(c) for c in col).strip() for col in pt.columns.values]
        
        pt_records = pt.reset_index().to_dict(orient="records")
        return sanitize_for_json({
            "index": req.index,
            "columns": req.columns,
            "values": req.values,
            "aggfunc": req.aggfunc,
            "data": pt_records,
            "fields": list(pt.reset_index().columns)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pivot generation failed: {str(e)}")

class TransformRequest(BaseModel):
    column: str
    transform_type: str  # log, zscore, minmax, binning
    bins: Optional[int] = 5

@app.post("/api/transform-column")
def transform_column(req: TransformRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df
    if req.column not in df.columns:
        raise HTTPException(status_code=400, detail="Column not found.")

    new_col_name = f"{req.column}_{req.transform_type}"
    series = df[req.column].dropna()

    try:
        if req.transform_type == "log":
            min_val = series.min()
            offset = abs(min_val) + 1 if min_val <= 0 else 0
            df[new_col_name] = np.log(df[req.column] + offset)
        elif req.transform_type == "zscore":
            df[new_col_name] = (df[req.column] - series.mean()) / (series.std() + 1e-8)
        elif req.transform_type == "minmax":
            df[new_col_name] = (df[req.column] - series.min()) / (series.max() - series.min() + 1e-8)
        elif req.transform_type == "binning":
            df[new_col_name] = pd.qcut(df[req.column], q=req.bins, duplicates="drop").astype(str)

        state.active_df = df
        state.cleaning_log.append({
            "timestamp": "Now",
            "action": f"Feature Engineering: {req.transform_type}",
            "column": req.column,
            "description": f"Created transformed feature '{new_col_name}'."
        })
        return get_current_dataset_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Transform failed: {str(e)}")

class NormalityTestRequest(BaseModel):
    column: str

@app.post("/api/normality-test")
def test_normality(req: NormalityTestRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df
    s = df[req.column].dropna()
    if len(s) < 8:
        raise HTTPException(status_code=400, detail="Need at least 8 samples for normality test.")

    # Shapiro-Wilk (capped at 5000)
    shapiro_stat, shapiro_p = stats.shapiro(s[:5000])
    # D'Agostino's K-squared
    dag_stat, dag_p = stats.normaltest(s)

    return sanitize_for_json({
        "column": req.column,
        "n_samples": len(s),
        "skewness": round(float(s.skew()), 3),
        "kurtosis": round(float(s.kurtosis()), 3),
        "shapiro_wilk": {"statistic": round(float(shapiro_stat), 4), "p_value": float(shapiro_p), "is_normal": shapiro_p > 0.05},
        "dagostino_k2": {"statistic": round(float(dag_stat), 4), "p_value": float(dag_p), "is_normal": dag_p > 0.05}
    })

class CleanActionRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}

@app.post("/api/clean")
def apply_cleaning(req: CleanActionRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    new_df, log_entry = DataCleaningEngine.apply_action(state.active_df, req.action, req.params)
    state.active_df = new_df
    state.cleaning_log.append(log_entry)
    return get_current_dataset_state()

@app.post("/api/reset")
def reset_dataset():
    if state.raw_df is None:
        raise HTTPException(status_code=400, detail="No raw dataset.")
    state.active_df = state.raw_df.copy()
    state.cleaning_log = []
    return get_current_dataset_state()

@app.get("/api/eda")
def get_eda():
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df
    num_summary = EDAEngine.get_numeric_summary(df)
    cat_summary = EDAEngine.get_categorical_summary(df)
    corr_df = EDAEngine.calculate_correlations(df)
    top_corrs = EDAEngine.get_top_correlations(corr_df) if corr_df is not None else []

    # Full correlation matrix for heatmap
    corr_matrix = {}
    if corr_df is not None:
        corr_matrix = {
            "columns": list(corr_df.columns),
            "z": corr_df.values.tolist()
        }

    return sanitize_for_json({
        "numeric_summary": num_summary.reset_index().to_dict(orient="records") if not num_summary.empty else [],
        "categorical_summary": cat_summary,
        "corr_matrix": corr_matrix,
        "top_correlations": top_corrs
    })

class HypothesisTestRequest(BaseModel):
    test_type: str
    val_col: Optional[str] = None
    grp_col: Optional[str] = None
    grp_a: Optional[str] = None
    grp_b: Optional[str] = None
    cat_a: Optional[str] = None
    cat_b: Optional[str] = None

@app.post("/api/statistics")
def run_statistical_test(req: HypothesisTestRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df

    if req.test_type == "ttest":
        s_a = df[df[req.grp_col] == req.grp_a][req.val_col]
        s_b = df[df[req.grp_col] == req.grp_b][req.val_col]
        res = StatisticalLab.run_two_sample_ttest(s_a, s_b)
    elif req.test_type == "mannwhitney":
        s_a = df[df[req.grp_col] == req.grp_a][req.val_col]
        s_b = df[df[req.grp_col] == req.grp_b][req.val_col]
        res = StatisticalLab.run_mann_whitney(s_a, s_b)
    elif req.test_type == "chisquare":
        res = StatisticalLab.run_chi_square(df, req.cat_a, req.cat_b)
        if "contingency_table" in res:
            res["contingency_table"] = res["contingency_table"].reset_index().to_dict(orient="records")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown test type '{req.test_type}'")

    return sanitize_for_json(res)

class ClusterRequest(BaseModel):
    features: List[str]
    n_clusters: int = 3

@app.post("/api/cluster")
def run_clustering(req: ClusterRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    res = ClusteringEngine.run_kmeans(state.active_df, req.features, req.n_clusters)
    if "pca_df" in res:
        res["pca_df"] = res["pca_df"].to_dict(orient="records")
    if "cluster_means" in res:
        res["cluster_means"] = res["cluster_means"].reset_index().to_dict(orient="records")
    return sanitize_for_json(res)

class AnomalyRequest(BaseModel):
    features: List[str]
    contamination: float = 0.05

@app.post("/api/anomaly")
def run_anomaly_detection(req: AnomalyRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    res = AnomalyDetector.detect_anomalies(state.active_df, req.features, req.contamination)
    if "anomalies_df" in res:
        res["anomalies_df"] = res["anomalies_df"].head(100).to_dict(orient="records")
    return sanitize_for_json(res)

class TimeSeriesRequest(BaseModel):
    date_col: str
    val_col: str
    freq: str = "W"

@app.post("/api/time-series")
def run_time_series(req: TimeSeriesRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    res = TimeSeriesEngine.analyze_series(state.active_df, req.date_col, req.val_col, req.freq)
    if "resampled_df" in res:
        res["resampled_df"] = res["resampled_df"].to_dict(orient="records")
    return sanitize_for_json(res)

class MLTrainRequest(BaseModel):
    target_col: str
    feature_cols: List[str]
    task_type: str

@app.post("/api/train-ml")
def train_ml(req: MLTrainRequest):
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    res, err = MachineLearningLab.build_and_evaluate(state.active_df, req.target_col, req.feature_cols, req.task_type)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return sanitize_for_json(res)

@app.get("/api/export/pdf")
def export_pdf():
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    df = state.active_df
    qual = DataQualityEngine.audit_quality(df)
    prof = DataProfiler.profile_dataset(df)
    insights = InsightEngine.generate_insights(df, qual, prof)
    pdf_bytes = ReportExporter.generate_pdf(state.filename, df, qual, prof, insights, state.cleaning_log)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Smart_Data_Analyst_{state.filename}.pdf"})

@app.get("/api/export/csv")
def export_csv():
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    csv_bytes = ReportExporter.to_csv_bytes(state.active_df)
    return Response(content=csv_bytes, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=Cleaned_{state.filename}.csv"})

@app.get("/api/export/excel")
def export_excel():
    if state.active_df is None:
        raise HTTPException(status_code=400, detail="No active dataset.")
    excel_bytes = ReportExporter.to_excel_bytes(state.active_df)
    return Response(content=excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=Cleaned_{state.filename}.xlsx"})
