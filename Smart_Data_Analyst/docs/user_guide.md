# DataNova — User Guide & Viva Walkthrough

## Quickstart
1. Double-click `run_windows.bat` or run:
   ```bash
   streamlit run app.py
   ```
2. Navigate to `http://localhost:8501`.

## Navigation & Feature Workflows

### 1. Data Ingestion (Sidebar)
- Upload any tabular CSV, XLSX, or XLS file.
- Or select from the pre-bundled benchmarks: **Retail E-commerce Sales**, **Student Academic Performance**, or **Clinical Heart Disease**.

### 2. Overview Dashboard
- Immediate KPI metrics: Total records, attributes, quality score, duplicate count, missing rate.
- Inferred column type breakdown donut chart.

### 3. Data Quality Intelligence
- Transparent quality score out of 100 with deduction breakdowns.
- Missing rate rankings and 1.5×IQR numeric outlier identification.

### 4. Smart Cleaning
- Non-destructive: the original upload is preserved while operations apply to a working copy.
- View prioritized recommendations (e.g., deduplicate, drop constant column, impute missing values, cap outliers).
- Click to apply and view updated audit logs with full reset capabilities.

### 5. EDA Studio & Visualization Lab
- Descriptive summary table with skewness, variance, median, and zeros.
- Interactive Plotly distributions, box plots, scatter plots, and correlation heatmaps.

### 6. Auto Insights & ML Lab
- Rule-based statistical alerts (Observations, Warnings, Recommendations).
- Benchmark classification or regression models with confusion matrices and feature importance rankings.

### 7. Report Center
- Generate and download executive multi-page PDF reports.
- Export cleaned datasets as CSV or Excel (.xlsx) workbooks.

