# Architecture Specification — DataNova

## 1. System Overview
DataNova is built upon a modular, decoupled architecture adhering to clean software engineering principles. The architecture isolates dataset loading, schema inference, mathematical and statistical profiling, cleaning, dynamic visualization, machine learning, and multi-format reporting.

```
                  ┌────────────────────────────────────────┐
                  │       Streamlit Presentation Layer     │
                  │ (app.py + 10 Decoupled Domain Pages)   │
                  └──────────────────┬─────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  Data Loader &      │   │  Smart Cleaning &   │   │  ReportLab PDF &    │
│  Type Inference     │   │  Audit Engine       │   │  Export Manager     │
└──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
           │                         │                         │
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  Statistical EDA &  │   │  Dynamic Plotly     │   │  Predictive ML      │
│  Data Quality Audit │   │  Visualization Lab  │   │  Benchmark Engine   │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

## 2. Core Modules
- **`modules/data_loader.py`**: Robust input parsing with encoding detection, multi-sheet Excel ingestion, and delimiter sniffing.
- **`modules/data_profiler.py`**: Dynamic column role identification (Numeric, Categorical, Boolean, DateTime, Text, Identifier) and distribution metrics.
- **`modules/data_quality.py`**: 1.5×IQR outlier detection, zero-variance/constant column checks, missingness rate, and the DataNova Quality Score formula:
  $$Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)$$
- **`modules/data_cleaner.py`**: User-approved non-destructive transformations (median/mode imputation, IQR capping, deduplication, column pruning).
- **`modules/eda_engine.py`**: Descriptive stats, skewness, Pearson/Spearman correlation matrices, and group aggregations.
- **`modules/visualization.py`**: High-performance Plotly Express/Graph Objects builder with automated theme styling and large-data sampling.
- **`modules/insight_engine.py`**: Deterministic rule-based statistical observations, warnings, and recommendations without third-party APIs.
- **`modules/ml_engine.py`**: Automated classification and regression pipeline with SimpleImputer, StandardScaler, OneHotEncoder, and model benchmark comparisons.
- **`modules/report_generator.py`**: ReportLab two-pass `NumberedCanvas` builder generating multi-page executive PDF summaries.
- **`modules/export_manager.py`**: Cleaned data serialization to CSV, XLSX, and JSON.

