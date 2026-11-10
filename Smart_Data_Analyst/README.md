# SMART DATA ANALYST — ENTERPRISE DATA ANALYTICS WEB PLATFORM
### Modern React 19 + Tailwind CSS + Recharts + FastAPI Engine

[![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20Tailwind-61dafb.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Uvicorn-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776ab.svg)](https://python.org)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-f7931e.svg)](https://scikit-learn.org)
[![ReportLab](https://img.shields.io/badge/Reports-ReportLab%20PDF-e11d48.svg)](https://www.reportlab.com)

**Smart Data Analyst** is a dataset-independent, full-stack analytics SaaS platform engineered with a modern web architecture:
- **Frontend**: React 19, Vite, Tailwind CSS 3.4, Recharts, Lucide Icons (Deep Midnight enterprise theme).
- **Backend**: Asynchronous FastAPI server executing pandas, NumPy, SciPy, scikit-learn, and ReportLab pipelines.

---

## 🌟 System Architecture

```text
┌────────────────────────────────────────────────────────┐
│           React Modern Web Application                 │
│      (Vite + Tailwind CSS + Recharts + Lucide)         │
│          http://localhost:3000                         │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON)
┌───────────────────────────▼────────────────────────────┐
│              FastAPI Python Engine                     │
│         (DataProfiler, Quality, EDA, ML)               │
│          http://127.0.0.1:8000                         │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 12 Full-Spectrum Analytics Modules

1. **Executive Dashboard**: Top-level KPI cards, interactive attribute role donut charts, health audits, and automated empirical observations.
2. **Data Explorer & Slicers**: Multivariable live categorical slicers, global search, column profile inspector, and interactive data table.
3. **Quality & Outliers**: 4-vector deduction formula breakdown ($Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)$), missingness bar chart ranking, Tukey IQR fences table with direct Winsorization (capping), and Shapiro-Wilk & D'Agostino normality testing.
4. **Smart Cleaning & Transforms**: Mathematical feature transforms ($\log(x)$, Z-score standardization, quantile binning), row deduplication, median imputation, and audit trails.
5. **Custom Visualizer Lab**: Dynamic chart builder supporting Bar, Line, Area, and Scatter charts with selectable dimensions, measures, and aggregations (Mean/Sum).
6. **Dynamic Pivot Matrix**: Multi-index grouping with companion Pivot Visual Breakdown Chart and tabular results.
7. **Statistical Correlation EDA**: Pairwise Pearson correlation heatmap grid, descriptive statistical matrices, and categorical frequency distribution bar charts.
8. **Hypothesis Testing Lab**: Welch's two-sample t-test, Mann-Whitney U, and Chi-Square independence tests with exact statistics, p-values, and narrative interpretations.
9. **K-Means & Anomaly ML**: Configurable K-Means clustering with 2D PCA projection scatter plots + Isolation Forest unsupervised anomaly detection.
10. **Temporal Velocity & Trend**: Chronological detection, daily/weekly/monthly resampling, moving averages, and period-over-period growth velocity charts.
11. **Predictive ML Workbench**: Leakage-free baseline modeling for both Classification and Regression with horizontal Feature Importance charts.
12. **Executive Export Center**: 1-click downloads for publication-grade ReportLab PDF briefs, cleaned CSVs, and Excel (`.xlsx`) workbooks.

---

## 🛠️ Launch & Verification Instructions

### 1. Launch FastAPI Backend
```powershell
python -m uvicorn server:app --port 8000
```
API docs: `http://127.0.0.1:8000/docs`

### 2. Launch React Frontend
```powershell
cd frontend
npm run preview -- --port 3000 --host
# Or for live hot-reload development:
npm run dev
```
Web app: `http://localhost:3000`

### 3. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
All 19 tests in `tests/test_smart_analyst.py` and `tests/edge_cases/test_edge_cases.py` pass.
