# Testing Specification & Verification Plan

## Test Suite Execution
DataNova uses `pytest` for automated unit and integration tests.

### How to Run Tests
```bash
python -m pytest tests/test_data_engine.py -v
```

### Verified Test Cases
1. **`test_data_loader_csv`**: Ingests UTF-8 CSV with automated delimiter sniffing and column sanitization.
2. **`test_data_loader_empty`**: Validates graceful rejection of 0-byte files with user-friendly errors.
3. **`test_data_profiler`**: Verifies dynamic type inference (Numeric, Boolean, Text, Categorical) and summary statistics.
4. **`test_data_quality_audit`**: Verifies 4-vector score formula $Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)$ and 1.5×IQR bounds.
5. **`test_data_cleaner_duplicates`**: Confirms exact duplicate removal without modifying original raw data.
6. **`test_data_cleaner_impute`**: Tests numeric median imputation.
7. **`test_data_cleaner_cap_outliers`**: Verifies Winsorization capping to upper/lower bounds.
8. **`test_eda_engine`**: Validates skewness, variance, quantile calculations, and correlation matrix.
9. **`test_ml_engine_classification`**: Validates classification model benchmarking (Decision Tree, Logistic Regression, Random Forest).
10. **`test_ml_engine_regression`**: Validates regression metrics ($R^2$, MAE, RMSE).
11. **`test_export_manager`**: Confirms CSV, Excel (OpenPyXL), and JSON serialization.
12. **`test_report_generator`**: Tests ReportLab two-pass `NumberedCanvas` PDF generation.

