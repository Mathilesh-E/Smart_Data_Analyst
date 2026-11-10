from __future__ import annotations

import io
import json
import logging
import math
import re
import uuid
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from scipy import stats

from smart_analyst.core import clean, diagnostics, insights, kind, profile, recommendations
from smart_analyst.report import pdf_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_data_analyst")

app = FastAPI(title="Smart Data Analyst", version="2.0.0")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ROWS = 1_000_000
workspaces: dict[str, dict[str, Any]] = {}
SAMPLES = {
    "retail_sales.csv": "Retail sales",
    "customer_churn.csv": "Customer churn & retention",
    "marketing_campaigns.csv": "Marketing & ad spend",
    "housing_prices.csv": "Real estate & housing",
    "stock_market.csv": "Financial time series",
    "healthcare_sample.csv": "Healthcare records",
    "flight_delays.csv": "Flight operations",
    "student_performance.csv": "Education performance",
}


class CleanRequest(BaseModel):
    actions: list[dict[str, str]] = Field(default_factory=list)


class FilterClause(BaseModel):
    column: str
    operator: Literal["eq", "ne", "contains", "gt", "gte", "lt", "lte", "between", "is_null", "not_null"] = "eq"
    value: Any = None
    value_to: Any = None


class ChartRequest(BaseModel):
    chart: str
    x: str | None = None
    y: str | None = None
    color: str | None = None
    aggregation: str = "mean"
    date_frequency: str = "auto"
    limit: int = Field(default=30, ge=5, le=100)
    filters: list[FilterClause] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    operation: Literal["describe", "group_summary", "crosstab", "pivot_table", "correlation", "missingness", "outliers", "frequency", "duplicates"]
    columns: list[str] = Field(default_factory=list)
    group_by: str | None = None
    column_by: str | None = None
    statistic: Literal["mean", "median", "sum", "count", "min", "max", "std"] = "mean"
    method: Literal["pearson", "spearman", "iqr", "zscore"] = "pearson"


class StatsRequest(BaseModel):
    test: str
    x: str
    y: str | None = None
    group: str | None = None


class ClusterRequest(BaseModel):
    columns: list[str]
    clusters: int = Field(default=3, ge=2, le=8)
    contamination: float = Field(default=0.03, ge=0.01, le=0.15)
    method: str = "cluster"


class TimeSeriesRequest(BaseModel):
    date: str
    value: str
    frequency: str = "MS"
    aggregation: str = "mean"


class MLRequest(BaseModel):
    task: str
    target: str
    features: list[str]
    test_size: float = Field(default=0.2, ge=0.15, le=0.4)


def workspace_for(workspace_id: str | None) -> dict[str, Any]:
    if not workspace_id or workspace_id not in workspaces:
        raise HTTPException(status_code=404, detail="No dataset is loaded in this workspace.")
    return workspaces[workspace_id]


def read_upload(content: bytes, filename: str) -> pd.DataFrame:
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Files must be 50 MB or smaller.")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".csv":
            try:
                frame = pd.read_csv(io.BytesIO(content), low_memory=False, on_bad_lines="error")
            except UnicodeDecodeError:
                frame = pd.read_csv(io.BytesIO(content), encoding="latin-1", low_memory=False, on_bad_lines="error")
        elif suffix in {".xlsx", ".xls"}:
            frame = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=415, detail="Upload a CSV, XLSX, or XLS file.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.info("File parsing failed for %s: %s", filename, exc)
        raise HTTPException(status_code=400, detail=f"Could not parse this file: {exc}") from exc
    if frame.empty:
        raise HTTPException(status_code=400, detail="This file has no data rows.")
    if len(frame) > MAX_ROWS:
        raise HTTPException(status_code=413, detail="The limit is 1,000,000 rows per upload.")
    names: list[str] = []
    seen: dict[str, int] = {}
    for index, value in enumerate(frame.columns):
        name = str(value).strip()
        if not name or re.fullmatch(r"Unnamed:\s*\d+", name, flags=re.IGNORECASE):
            name = f"unnamed_{index + 1}"
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    frame.columns = names
    return frame


def normalize_types(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, set[Any]]]:
    working = frame.copy(deep=True)
    invalid: dict[str, set[Any]] = {}
    for column in working.columns:
        inferred = kind(frame[column])
        if inferred == "numeric":
            converted = pd.to_numeric(frame[column], errors="coerce")
            invalid_mask = frame[column].notna() & (converted.isna() | np.isinf(converted))
            converted = converted.replace([np.inf, -np.inf], np.nan)
            if invalid_mask.any():
                invalid[column] = set(frame.index[invalid_mask])
            working[column] = converted
        elif inferred == "datetime" and not pd.api.types.is_datetime64_any_dtype(frame[column]):
            converted = pd.to_datetime(frame[column], errors="coerce", format="mixed")
            invalid[column] = set(frame.index[frame[column].notna() & converted.isna()])
            working[column] = converted
    return working, {column: rows for column, rows in invalid.items() if rows}


def current_profile(state: dict[str, Any]) -> dict[str, Any]:
    result = profile(state["data"])
    result["kinds"].update(state.get("type_overrides", {}))
    result["numeric"] = [c for c in state["data"] if result["kinds"][c] == "numeric"]
    result["categorical"] = [c for c in state["data"] if result["kinds"][c] in ("categorical", "boolean")]
    result["dates"] = [c for c in state["data"] if result["kinds"][c] == "datetime"]
    result["identifiers"] = [c for c in state["data"] if result["kinds"][c] == "identifier"]
    for column in result["schema"]:
        name = column["Column"]
        column["Type"] = result["kinds"][name]
        column["Invalid values"] = len(state.get("invalid_positions", {}).get(name, set()))
        if column["Type"] == "numeric":
            values = pd.to_numeric(state["data"][name], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if len(values):
                column.update({"Minimum": float(values.min()), "Maximum": float(values.max()), "Mean": float(values.mean()), "Median": float(values.median()), "Std dev": float(values.std()) if len(values) > 1 else 0.0, "25th percentile": float(values.quantile(.25)), "75th percentile": float(values.quantile(.75))})
        elif column["Type"] == "datetime":
            values = pd.to_datetime(state["data"][name], errors="coerce").dropna()
            if len(values):
                column.update({"Minimum": values.min().isoformat(), "Maximum": values.max().isoformat()})
        else:
            column.update({"Minimum": None, "Maximum": None, "Mean": None, "Median": None, "Std dev": None, "25th percentile": None, "75th percentile": None})
        if column["Type"] in ("categorical", "boolean"):
            modes = state["data"][name].mode(dropna=True)
            column["Most frequent"] = str(modes.iloc[0]) if len(modes) else None
        elif column["Type"] not in ("numeric",):
            column["Most frequent"] = None
    return result


def json_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def table_rows(frame: pd.DataFrame, start: int = 0, limit: int = 50) -> list[dict[str, Any]]:
    return [
        {str(key): json_value(value) for key, value in row.items()}
        for row in frame.iloc[start : start + limit].to_dict(orient="records")
    ]


def apply_filters(frame: pd.DataFrame, filters: list[FilterClause]) -> pd.DataFrame:
    filtered = frame
    for clause in filters:
        if clause.column not in filtered:
            raise HTTPException(status_code=400, detail=f"Unknown filter column: {clause.column}.")
        series = filtered[clause.column]
        if clause.operator == "is_null":
            mask = series.isna()
        elif clause.operator == "not_null":
            mask = series.notna()
        elif clause.operator == "contains":
            mask = series.astype("string").str.contains(str(clause.value or ""), case=False, na=False, regex=False)
        elif clause.operator in {"eq", "ne"} and pd.api.types.is_datetime64_any_dtype(series):
            try:
                date_value = pd.to_datetime(clause.value, errors="raise")
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail=f"Filter value for {clause.column} must be a valid date.")
            dates = pd.to_datetime(series, errors="coerce")
            equal = dates.dt.date == date_value.date()
            mask = equal if clause.operator == "eq" else ~equal
        elif clause.operator in {"eq", "ne"} and pd.api.types.is_numeric_dtype(series):
            try:
                number = float(clause.value)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail=f"Filter value for {clause.column} must be numeric.")
            numeric = pd.to_numeric(series, errors="coerce")
            mask = numeric.eq(number) if clause.operator == "eq" else numeric.ne(number)
        elif clause.operator in {"gt", "gte", "lt", "lte", "between"}:
            numeric = pd.to_numeric(series, errors="coerce")
            try:
                first = float(clause.value)
                if clause.operator == "gt":
                    mask = numeric > first
                elif clause.operator == "gte":
                    mask = numeric >= first
                elif clause.operator == "lt":
                    mask = numeric < first
                elif clause.operator == "lte":
                    mask = numeric <= first
                else:
                    mask = numeric.between(first, float(clause.value_to))
            except (TypeError, ValueError):
                dates = pd.to_datetime(series, errors="coerce", format="mixed")
                try:
                    first_date = pd.to_datetime(clause.value, errors="raise")
                    second_date = pd.to_datetime(clause.value_to, errors="raise") if clause.operator == "between" else None
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail=f"Filter value for {clause.column} must be numeric or a valid date.")
                if clause.operator == "gt":
                    mask = dates > first_date
                elif clause.operator == "gte":
                    mask = dates >= first_date
                elif clause.operator == "lt":
                    mask = dates < first_date
                elif clause.operator == "lte":
                    mask = dates <= first_date
                else:
                    mask = dates.between(first_date, second_date)
        else:
            comparison = series.astype("string")
            value = str(clause.value)
            mask = comparison == value if clause.operator == "eq" else comparison != value
        filtered = filtered.loc[mask.fillna(False)]
    return filtered


def overview_payload(state: dict[str, Any]) -> dict[str, Any]:
    frame = state["data"]
    result = current_profile(state)
    number_data = frame[result["numeric"]].replace([np.inf, -np.inf], np.nan) if result["numeric"] else pd.DataFrame()
    missing = [{"column": c, "count": int(frame[c].isna().sum())} for c in frame if frame[c].isna().any()]
    missing.sort(key=lambda item: item["count"], reverse=True)
    distribution = frame[result["numeric"]].describe().to_dict() if result["numeric"] else {}
    correlations: list[dict[str, Any]] = []
    if len(result["numeric"]) > 1:
        matrix = number_data.corr()
        for i, first in enumerate(matrix.columns):
            for second in matrix.columns[i + 1 :]:
                corr = matrix.loc[first, second]
                if pd.notna(corr):
                    correlations.append({"x": first, "y": second, "value": round(float(corr), 3)})
    categorical = []
    for column in result["categorical"][:4]:
        values = frame[column].astype("string").fillna("(Missing)").value_counts().head(8)
        categorical.append({"column": column, "values": [{"name": str(k), "value": int(v)} for k, v in values.items()]})
    numeric_distributions = []
    for column in result["numeric"][:3]:
        values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            continue
        counts, edges = np.histogram(values, bins=min(18, max(5, int(math.sqrt(len(values))))))
        numeric_distributions.append({
            "column": column,
            "values": [{"name": f"{edges[i]:.3g}–{edges[i + 1]:.3g}", "value": int(counts[i])} for i in range(len(counts))],
        })
    date_trends = []
    if result["dates"] and result["numeric"]:
        date_column, measure = result["dates"][0], result["numeric"][0]
        trend = frame[[date_column, measure]].copy()
        trend[date_column] = pd.to_datetime(trend[date_column], errors="coerce")
        trend[measure] = pd.to_numeric(trend[measure], errors="coerce")
        trend = trend.dropna().groupby(date_column, dropna=True)[measure].mean().sort_index()
        if not trend.empty:
            stride = max(1, math.ceil(len(trend) / 60))
            date_trends.append({
                "date": date_column,
                "measure": measure,
                "values": [{"name": timestamp.isoformat()[:10], "value": json_value(value)} for timestamp, value in trend.iloc[::stride].items()],
            })
    diagnostics_rows = diagnostics(frame, result).to_dict(orient="records")
    for row in diagnostics_rows:
        row["Invalid values"] = len(state.get("invalid_positions", {}).get(row["Column"], set()))
    observations = [{"level": level, "title": title, "detail": detail} for level, title, detail in insights(frame, result)]
    invalid_count = sum(len(rows) for rows in state.get("invalid_positions", {}).values())
    if invalid_count:
        observations.insert(0, {
            "level": "warning",
            "title": "Invalid inferred values",
            "detail": f"{invalid_count:,} non-empty values could not be parsed as their inferred numeric or date type. They are shown as missing in the working copy; the original upload is preserved.",
        })
    return {
        "profile": {**result, "filename": state["name"], "file_size": state["size"]},
        "diagnostics": diagnostics_rows,
        "insights": observations,
        "missing": missing[:12],
        "correlations": sorted(correlations, key=lambda x: abs(x["value"]), reverse=True)[:40],
        "categorical": categorical,
        "numeric_distributions": numeric_distributions,
        "date_trends": date_trends,
        "numeric_summary": distribution,
        "cleaning_history": state["history"],
        "invalid_values": invalid_count,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/samples")
def list_samples() -> list[dict[str, str]]:
    return [{"file": name, "label": label} for name, label in SAMPLES.items()]


@app.post("/api/samples/{filename}")
def load_sample(filename: str, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    if filename not in SAMPLES:
        raise HTTPException(status_code=404, detail="Sample dataset not found.")
    path = Path(__file__).parent / "sample_data" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="The sample dataset file is missing.")
    state = create_workspace(path.read_bytes(), filename)
    return {"workspace_id": state["id"], "overview": overview_payload(state)}


@app.post("/api/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    x_workspace_id: str | None = Header(default=None),
) -> dict[str, Any]:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    state = create_workspace(content, file.filename or "dataset.csv")
    return {"workspace_id": state["id"], "overview": overview_payload(state)}


def create_workspace(content: bytes, filename: str) -> dict[str, Any]:
    original = read_upload(content, filename)
    frame, invalid_positions = normalize_types(original)
    workspace_id = str(uuid.uuid4())
    state = {
        "id": workspace_id,
        "name": Path(filename).name,
        "size": len(content),
        "original": original.copy(deep=True),
        "original_working": frame.copy(deep=True),
        "data": frame.copy(deep=True),
        "invalid_positions": invalid_positions,
        "history": [],
        "type_overrides": {},
        "analysis": {},
    }
    workspaces[workspace_id] = state
    return state


@app.get("/api/overview")
def overview(x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    return overview_payload(workspace_for(x_workspace_id))


@app.get("/api/table")
def get_table(
    offset: int = 0,
    limit: int = 50,
    search: str = "",
    x_workspace_id: str | None = Header(default=None),
) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    if search:
        mask = frame.astype("string").apply(lambda col: col.str.contains(search, case=False, na=False, regex=False)).any(axis=1)
        frame = frame.loc[mask]
    return {
        "rows": table_rows(frame, max(0, offset), min(max(limit, 1), 200)),
        "total": len(frame),
        "columns": list(frame.columns),
        "offset": offset,
    }


@app.get("/api/cleaning")
def cleaning_options(x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    p = current_profile(state)
    return {"recommendations": recommendations(state["data"], p), "history": state["history"]}


@app.post("/api/cleaning/preview")
def preview_cleaning(request: CleanRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    preview, log = clean(state["data"], request.actions)
    return {
        "before": {"rows": len(state["data"]), "columns": state["data"].shape[1]},
        "after": {"rows": len(preview), "columns": preview.shape[1]},
        "changes": log,
        "preview": table_rows(preview, 0, 12),
    }


@app.post("/api/cleaning/apply")
def apply_cleaning(request: CleanRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    updated, log = clean(state["data"], request.actions)
    if not log:
        raise HTTPException(status_code=400, detail="No valid cleaning actions were selected.")
    state["data"] = updated
    state["history"].extend(log)
    for column, positions in state["invalid_positions"].items():
        state["invalid_positions"][column] = {
            index for index in positions
            if index in updated.index and pd.isna(updated.loc[index, column])
        }
    return overview_payload(state)


@app.post("/api/reset")
def reset_workspace(x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    state["data"] = state["original_working"].copy(deep=True)
    state["history"] = []
    state["analysis"] = {}
    _, state["invalid_positions"] = normalize_types(state["original"])
    return overview_payload(state)


@app.put("/api/types")
def update_types(
    updates: dict[str, str],
    x_workspace_id: str | None = Header(default=None),
) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    accepted = {"numeric", "categorical", "boolean", "datetime", "identifier", "text", "empty"}
    for column, value in updates.items():
        if column not in state["data"].columns or value not in accepted:
            raise HTTPException(status_code=400, detail=f"Invalid type update for {column}.")
    state["type_overrides"].update(updates)
    return overview_payload(state)


@app.get("/api/controls")
def analysis_controls(x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    profile_data = current_profile(state)
    controls = []
    for column in frame.columns:
        values = frame[column].dropna()
        item: dict[str, Any] = {"column": column, "kind": profile_data["kinds"][column]}
        if item["kind"] in {"categorical", "boolean", "identifier"}:
            item["options"] = [str(value) for value in values.astype("string").value_counts().head(100).index]
            item["truncated"] = values.nunique() > 100
        elif item["kind"] == "numeric":
            numeric = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if len(numeric):
                item.update({"minimum": json_value(numeric.min()), "maximum": json_value(numeric.max())})
        elif item["kind"] == "datetime":
            dates = pd.to_datetime(values, errors="coerce", format="mixed").dropna()
            if len(dates):
                item.update({"minimum": dates.min().isoformat(), "maximum": dates.max().isoformat()})
        controls.append(item)
    return {"columns": controls}


@app.post("/api/analysis")
def run_analysis(request: AnalysisRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    selected = list(dict.fromkeys(request.columns))
    if any(column not in frame.columns for column in selected):
        raise HTTPException(status_code=400, detail="One or more selected columns are not in this dataset.")
    profile_data = current_profile(state)
    if request.operation == "describe":
        columns = selected or list(frame.columns)
        if len(columns) > 30:
            raise HTTPException(status_code=400, detail="Select at most 30 columns for a descriptive profile.")
        output = []
        for column in columns:
            values = frame[column]
            item = {
                "Column": column,
                "Type": profile_data["kinds"][column],
                "Records": len(values),
                "Missing": int(values.isna().sum()),
                "Missing %": round(float(values.isna().mean() * 100), 2),
                "Unique": int(values.nunique(dropna=True)),
            }
            if item["Type"] == "numeric":
                numeric = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
                item.update({
                    "Mean": json_value(numeric.mean()) if len(numeric) else None,
                    "Median": json_value(numeric.median()) if len(numeric) else None,
                    "Std dev": json_value(numeric.std()) if len(numeric) > 1 else None,
                    "Minimum": json_value(numeric.min()) if len(numeric) else None,
                    "25th percentile": json_value(numeric.quantile(.25)) if len(numeric) else None,
                    "75th percentile": json_value(numeric.quantile(.75)) if len(numeric) else None,
                    "Maximum": json_value(numeric.max()) if len(numeric) else None,
                    "Skew": json_value(numeric.skew()) if len(numeric) > 2 else None,
                })
            elif item["Type"] == "datetime":
                dates = pd.to_datetime(values, errors="coerce", format="mixed").dropna()
                item.update({"Minimum": dates.min().isoformat() if len(dates) else None, "Maximum": dates.max().isoformat() if len(dates) else None})
            else:
                modes = values.mode(dropna=True)
                item["Most frequent"] = json_value(modes.iloc[0]) if len(modes) else None
                item["Most frequent count"] = int(values.value_counts(dropna=True).iloc[0]) if len(values.value_counts(dropna=True)) else 0
            output.append(item)
        return {"operation": request.operation, "title": "Descriptive statistics", "columns": list(output[0]) if output else [], "rows": output, "records_analyzed": len(frame)}

    if request.operation == "group_summary":
        if request.group_by not in frame:
            raise HTTPException(status_code=400, detail="Choose a valid grouping column.")
        numeric_columns = [column for column in selected if profile_data["kinds"][column] == "numeric" and column != request.group_by]
        if not numeric_columns:
            raise HTTPException(status_code=400, detail="Choose at least one numeric measure different from the grouping column.")
        data = frame[[request.group_by, *numeric_columns]].copy()
        data[request.group_by] = data[request.group_by].astype("string").fillna("(Missing)")
        for column in numeric_columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        grouped = data.groupby(request.group_by, dropna=False, observed=False)
        if request.statistic == "count":
            summary = grouped[numeric_columns].count()
        else:
            summary = getattr(grouped[numeric_columns], request.statistic)()
        summary = summary.sort_values(numeric_columns[0], ascending=False, na_position="last").head(100)
        rows = [{"Group": str(index), **{column: json_value(value) for column, value in row.items()}} for index, row in summary.iterrows()]
        return {"operation": request.operation, "title": f"{request.statistic.title()} by {request.group_by}", "columns": ["Group", *numeric_columns], "rows": rows, "groups": len(rows)}

    if request.operation == "crosstab":
        if len(selected) != 2 or selected[0] == selected[1]:
            raise HTTPException(status_code=400, detail="Choose exactly two different categorical columns.")
        first, second = selected
        left = frame[first].astype("string").fillna("(Missing)")
        right = frame[second].astype("string").fillna("(Missing)")
        keep_left = left.value_counts().head(30).index
        keep_right = right.value_counts().head(30).index
        counts = pd.crosstab(left.where(left.isin(keep_left), "(Other)"), right.where(right.isin(keep_right), "(Other)"))
        rows = [{"Category": str(index), **{str(column): int(value) for column, value in row.items()}} for index, row in counts.iterrows()]
        return {"operation": request.operation, "title": f"{first} × {second}", "columns": ["Category", *[str(column) for column in counts.columns]], "rows": rows, "truncated": left.nunique() > 30 or right.nunique() > 30}

    if request.operation == "pivot_table":
        if request.group_by not in frame or request.column_by not in frame or request.group_by == request.column_by:
            raise HTTPException(status_code=400, detail="Choose two different pivot dimensions.")
        numeric_columns = [column for column in selected if profile_data["kinds"][column] == "numeric"]
        if len(numeric_columns) != 1:
            raise HTTPException(status_code=400, detail="Choose exactly one numeric measure for the pivot table.")
        row_labels = frame[request.group_by].astype("string").fillna("(Missing)")
        column_labels = frame[request.column_by].astype("string").fillna("(Missing)")
        keep_rows = row_labels.value_counts().head(15).index
        keep_columns = column_labels.value_counts().head(15).index
        values = pd.to_numeric(frame[numeric_columns[0]], errors="coerce").replace([np.inf, -np.inf], np.nan)
        pivot_data = pd.DataFrame({
            "rows": row_labels.where(row_labels.isin(keep_rows), "(Other)"),
            "columns": column_labels.where(column_labels.isin(keep_columns), "(Other)"),
            "value": values,
        })
        pivot = pd.pivot_table(pivot_data, index="rows", columns="columns", values="value", aggfunc=request.statistic, fill_value=0)
        rows = [{"Group": str(index), **{str(column): json_value(value) for column, value in row.items()}} for index, row in pivot.iterrows()]
        return {
            "operation": request.operation,
            "title": f"{request.statistic.title()} of {numeric_columns[0]} · {request.group_by} × {request.column_by}",
            "columns": ["Group", *[str(column) for column in pivot.columns]],
            "rows": rows,
            "truncated": row_labels.nunique() > 15 or column_labels.nunique() > 15,
        }

    if request.operation == "correlation":
        columns = [column for column in selected if profile_data["kinds"][column] == "numeric"]
        if len(columns) < 2:
            raise HTTPException(status_code=400, detail="Select at least two numeric columns.")
        if len(columns) > 30:
            raise HTTPException(status_code=400, detail="Select at most 30 numeric columns.")
        numeric = frame[columns].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        matrix = numeric.corr(method=request.method).fillna(0)
        counts = numeric.notna().astype(int).T.dot(numeric.notna().astype(int))
        return {
            "operation": request.operation,
            "title": f"{request.method.title()} correlation",
            "columns": columns,
            "matrix": [[json_value(value) for value in row] for row in matrix.to_numpy()],
            "pair_counts": counts.to_numpy().tolist(),
            "records_analyzed": len(numeric),
            "warning": "Correlations are pairwise associations, not causal effects.",
        }

    if request.operation == "missingness":
        rows = []
        for column in frame.columns:
            count = int(frame[column].isna().sum())
            rows.append({"Column": column, "Missing": count, "Present": int(len(frame) - count), "Missing %": round(count / len(frame) * 100, 2) if len(frame) else 0, "Type": profile_data["kinds"][column]})
        rows.sort(key=lambda row: row["Missing"], reverse=True)
        return {"operation": request.operation, "title": "Missing-value audit", "columns": ["Column", "Type", "Missing", "Present", "Missing %"], "rows": rows, "rows_with_missing": int(frame.isna().any(axis=1).sum()), "complete_rows": int(frame.notna().all(axis=1).sum())}

    if request.operation == "outliers":
        columns = [column for column in selected if profile_data["kinds"][column] == "numeric"]
        if not columns:
            raise HTTPException(status_code=400, detail="Choose at least one numeric column.")
        rows = []
        for column in columns:
            values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
            valid = values.dropna()
            if not len(valid):
                continue
            if request.method == "zscore":
                center, spread = valid.mean(), valid.std(ddof=0)
                lower, upper = center - 3 * spread, center + 3 * spread
            else:
                q1, q3 = valid.quantile([.25, .75])
                spread = q3 - q1
                lower, upper = q1 - 1.5 * spread, q3 + 1.5 * spread
            mask = values.lt(lower) | values.gt(upper)
            rows.append({"Column": column, "Method": request.method.upper(), "Valid values": len(valid), "Potential outliers": int(mask.sum()), "Outlier %": round(float(mask.mean() * 100), 2), "Lower bound": json_value(lower), "Upper bound": json_value(upper)})
        return {"operation": request.operation, "title": f"Potential outliers · {request.method.upper()}", "columns": list(rows[0]) if rows else [], "rows": rows, "warning": "These are review candidates, not automatically invalid records. No values were changed."}

    if request.operation == "frequency":
        if len(selected) != 1:
            raise HTTPException(status_code=400, detail="Choose one field for a frequency table.")
        column = selected[0]
        counts = frame[column].astype("string").fillna("(Missing)").value_counts().head(100)
        total = int(counts.sum())
        rows = []
        cumulative = 0
        for label, count in counts.items():
            cumulative += int(count)
            rows.append({"Value": str(label), "Count": int(count), "Percent": round(int(count) / len(frame) * 100, 2), "Cumulative %": round(cumulative / len(frame) * 100, 2)})
        return {"operation": request.operation, "title": f"Frequency · {column}", "columns": ["Value", "Count", "Percent", "Cumulative %"], "rows": rows, "distinct_values": int(frame[column].nunique(dropna=False)), "truncated": frame[column].nunique(dropna=False) > 100}

    duplicate_mask = frame.duplicated(keep="first")
    return {"operation": request.operation, "title": "Duplicate-record audit", "columns": list(frame.columns), "rows": table_rows(frame.loc[duplicate_mask], 0, 100), "duplicate_rows": int(duplicate_mask.sum()), "duplicate_members": int(frame.duplicated(keep=False).sum()), "records_analyzed": len(frame), "truncated": int(duplicate_mask.sum()) > 100}


@app.post("/api/chart")
def chart_data(request: ChartRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    original = state["data"]
    frame = apply_filters(original, request.filters)
    if frame.empty:
        raise HTTPException(status_code=400, detail="No records match the selected slicers.")
    if request.chart != "correlation" and request.x not in frame.columns:
        raise HTTPException(status_code=400, detail="Select a valid X-axis column.")
    if request.color and request.color not in frame.columns:
        raise HTTPException(status_code=400, detail="Select a valid series/color column.")
    sample = frame.sample(50_000, random_state=42) if len(frame) > 50_000 else frame
    counts_meta = {"records_before_filters": len(original), "records_after_filters": len(frame)}
    if request.chart == "histogram":
        values = pd.to_numeric(sample[request.x], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            raise HTTPException(status_code=400, detail=f"{request.x} has no usable numeric values for a histogram.")
        if values.min() == values.max():
            return {**counts_meta, "sampled": len(frame) > len(sample), "series": [{"name": str(json_value(values.iloc[0])), "value": int(len(values))}]}
        counts, edges = np.histogram(values, bins=min(request.limit, 50))
        return {**counts_meta, "sampled": len(frame) > len(sample), "series": [{"name": f"{edges[i]:.3g}–{edges[i + 1]:.3g}", "value": int(counts[i])} for i in range(len(counts))]}
    if request.chart in {"category", "pie", "donut"}:
        counts = sample[request.x].astype("string").fillna("(Missing)").value_counts().head(request.limit)
        return {**counts_meta, "sampled": len(frame) > len(sample), "series": [{"name": str(k), "value": int(v)} for k, v in counts.items()]}
    if request.chart == "correlation":
        p = current_profile(state)
        numeric_columns = [column for column in p["numeric"] if column in frame]
        if len(numeric_columns) < 2:
            raise HTTPException(status_code=400, detail="At least two numeric columns are needed.")
        values = frame[numeric_columns].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).corr().fillna(0)
        matrix = [[json_value(value) for value in row] for row in values.round(3).to_numpy()]
        return {**counts_meta, "columns": list(values.columns), "values": matrix, "sampled": False}
    if request.y not in frame.columns:
        raise HTTPException(status_code=400, detail="Select a valid Y-axis column.")
    if request.chart == "scatter":
        points = sample[[request.x, request.y]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        sampled = len(frame) > 50_000 or len(points) > 2_000
        if len(points) > 2000:
            points = points.sample(2000, random_state=42)
        return {
            **counts_meta,
            "sampled": sampled,
            "series": [{"x": json_value(x_value), "y": json_value(y_value)} for x_value, y_value in points.itertuples(index=False, name=None)],
        }
    if request.color:
        group_data = sample[[request.x, request.color, request.y]].copy()
        group_data[request.x] = group_data[request.x].astype("string").fillna("(Missing)")
        group_data[request.color] = group_data[request.color].astype("string").fillna("(Missing)")
        series_names = group_data[request.color].value_counts().head(8).index.tolist()
        group_data[request.color] = group_data[request.color].where(group_data[request.color].isin(series_names), "(Other)")
        grouped = group_data.groupby([request.x, request.color], dropna=False, observed=False)[request.y]
        aggregate = request.aggregation if request.aggregation in {"mean", "sum", "count", "median"} else "mean"
        aggregated = getattr(grouped, aggregate)().dropna().rename("value").reset_index()
        if request.chart == "bar":
            x_order = aggregated.groupby(request.x)["value"].sum().sort_values(ascending=False).head(request.limit).index
        else:
            x_order = aggregated[request.x].drop_duplicates().head(request.limit)
        aggregated = aggregated[aggregated[request.x].isin(x_order)]
        pivoted = aggregated.pivot(index=request.x, columns=request.color, values="value").reindex(x_order)
        return {
            **counts_meta,
            "sampled": len(frame) > len(sample),
            "series_names": [str(name) for name in series_names if name in pivoted.columns] + (["(Other)"] if "(Other)" in pivoted.columns else []),
            "series": [{"name": str(index), **{str(key): json_value(value) for key, value in row.items()}} for index, row in pivoted.iterrows()],
        }
    group = sample.groupby(request.x, dropna=False, observed=False)[request.y]
    aggregate = request.aggregation if request.aggregation in {"mean", "sum", "count", "median"} else "mean"
    values = getattr(group, aggregate)().dropna()
    if request.chart in {"line", "area"}:
        values = values.sort_index()
    elif request.chart == "bar":
        values = values.sort_values(ascending=False).head(request.limit)
    return {**counts_meta, "sampled": len(frame) > len(sample), "series": [{"name": str(k), "value": json_value(v)} for k, v in values.head(request.limit).items()]}


@app.post("/api/statistics")
def run_statistics(request: StatsRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    if request.x not in frame.columns:
        raise HTTPException(status_code=400, detail="Select a valid first variable.")
    try:
        if request.test == "chi_square":
            if request.group not in frame.columns or request.group == request.x:
                raise HTTPException(status_code=400, detail="Select two different categorical variables.")
            table = pd.crosstab(frame[request.x], frame[request.group])
            if table.shape[0] < 2 or table.shape[1] < 2:
                raise HTTPException(status_code=400, detail="Both fields need at least two observed categories.")
            statistic, p_value, degrees, _ = stats.chi2_contingency(table)
            effect = math.sqrt(float(statistic) / (int(table.to_numpy().sum()) * max(1, min(table.shape) - 1)))
            return {"test": "Chi-square test of independence", "n": int(table.to_numpy().sum()), "statistic": float(statistic), "p_value": float(p_value), "effect": effect, "degrees_freedom": int(degrees), "interpretation": "This tests whether the observed categories are associated. Check expected cell counts; association does not establish causation."}
        if request.test in {"pearson", "spearman"}:
            if request.y not in frame.columns or request.y == request.x:
                raise HTTPException(status_code=400, detail="Select two different numeric columns.")
            pair = frame[[request.x, request.y]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(pair) < 3:
                raise HTTPException(status_code=400, detail="At least 3 complete pairs are needed.")
            result = stats.pearsonr(pair.iloc[:, 0], pair.iloc[:, 1]) if request.test == "pearson" else stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1])
            return {"test": request.test.title(), "n": len(pair), "statistic": float(result.statistic), "p_value": float(result.pvalue), "effect": float(result.statistic), "interpretation": "Association only; this does not establish causation."}
        if request.test in {"welch", "mann_whitney", "kruskal"}:
            if request.group not in frame.columns:
                raise HTTPException(status_code=400, detail="Select a grouping column.")
            data = frame[[request.x, request.group]].copy()
            data[request.x] = pd.to_numeric(data[request.x], errors="coerce")
            groups = [part[request.x].dropna().to_numpy() for _, part in data.dropna(subset=[request.group]).groupby(request.group) if len(part[request.x].dropna()) >= 2]
            if len(groups) < 2:
                raise HTTPException(status_code=400, detail="At least two groups with two values each are needed.")
            if request.test in {"welch", "mann_whitney"} and len(groups) != 2:
                raise HTTPException(status_code=400, detail="This test requires exactly two groups.")
            if request.test == "welch":
                result = stats.ttest_ind(*groups, equal_var=False)
                pooled = math.sqrt((groups[0].var(ddof=1) + groups[1].var(ddof=1)) / 2)
                effect = (groups[0].mean() - groups[1].mean()) / pooled if pooled else None
            elif request.test == "mann_whitney":
                result = stats.mannwhitneyu(*groups, alternative="two-sided")
                effect = None
            else:
                result = stats.kruskal(*groups)
                effect = None
            return {"test": request.test.replace("_", " ").title(), "n": int(sum(map(len, groups))), "statistic": float(result.statistic), "p_value": float(result.pvalue), "effect": json_value(effect), "interpretation": "Exploratory result. Statistical significance is not practical significance; review assumptions and design."}
        raise HTTPException(status_code=400, detail="Choose a supported test.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not calculate this test: {exc}") from exc


@app.post("/api/ml")
def train_baseline(request: MLRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    state = workspace_for(x_workspace_id)
    frame = state["data"]
    if request.task not in {"classification", "regression"}:
        raise HTTPException(status_code=400, detail="Select classification or regression.")
    if request.target not in frame or not request.features or request.target in request.features:
        raise HTTPException(status_code=400, detail="Choose a target and at least one different feature.")
    if any(column not in frame for column in request.features):
        raise HTTPException(status_code=400, detail="A selected feature is not in this dataset.")
    if len(request.features) > 40:
        raise HTTPException(status_code=400, detail="Choose at most 40 features for this local baseline.")

    model_data = frame[request.features + [request.target]].dropna(subset=[request.target]).copy()
    if len(model_data) < 50:
        raise HTTPException(status_code=400, detail="At least 50 labelled rows are needed.")
    target = model_data[request.target]
    if request.task == "classification" and target.nunique() < 2:
        raise HTTPException(status_code=400, detail="Classification requires at least two target classes.")
    if request.task == "regression" and not pd.api.types.is_numeric_dtype(target):
        raise HTTPException(status_code=400, detail="Regression requires a numeric target.")
    if request.task == "classification" and target.nunique() > 30:
        raise HTTPException(status_code=400, detail="This target has too many classes for the classification baseline.")

    features = model_data[request.features].copy()
    empty_columns = [column for column in features if features[column].isna().all()]
    features = features.drop(columns=empty_columns)
    if not len(features.columns):
        raise HTTPException(status_code=400, detail="Every selected feature is empty.")
    num_columns = [column for column in features if pd.api.types.is_numeric_dtype(features[column])]
    cat_columns = [column for column in features if column not in num_columns]
    too_many = [column for column in cat_columns if features[column].nunique(dropna=True) > 1000]
    if too_many:
        raise HTTPException(status_code=400, detail=f"High-cardinality feature(s) are too large for one-hot encoding: {', '.join(too_many)}.")
    for column in cat_columns:
        features[column] = features[column].astype("object")

    transformers = []
    if num_columns:
        transformers.append(("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_columns))
    if cat_columns:
        transformers.append(("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore", max_categories=100))]), cat_columns))
    preprocessor = ColumnTransformer(transformers, remainder="drop")
    stratify = target if request.task == "classification" and target.value_counts().min() >= 2 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=request.test_size, random_state=42, stratify=stratify,
        )
        models = (
            [("Logistic regression", LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")), ("Random forest", RandomForestClassifier(n_estimators=120, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1))]
            if request.task == "classification"
            else [("Ridge regression", Ridge()), ("Random forest", RandomForestRegressor(n_estimators=120, min_samples_leaf=2, random_state=42, n_jobs=-1))]
        )
        results = []
        for label, estimator in models:
            pipeline = Pipeline([("preprocess", preprocessor), ("model", estimator)])
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            if request.task == "classification":
                row: dict[str, Any] = {
                    "model": label,
                    "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
                    "precision_weighted": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 4),
                    "recall_weighted": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 4),
                    "f1_weighted": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 4),
                }
                if target.nunique() == 2 and len(pd.unique(y_test)) == 2 and hasattr(pipeline, "predict_proba"):
                    row["roc_auc"] = round(float(roc_auc_score(y_test, pipeline.predict_proba(X_test)[:, 1])), 4)
                labels = [json_value(v) for v in pd.unique(target)]
                row["confusion"] = confusion_matrix(y_test, predictions, labels=pd.unique(target)).tolist()
                row["labels"] = labels
            else:
                row = {
                    "model": label,
                    "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
                    "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 4),
                    "r2": round(float(r2_score(y_test, predictions)), 4),
                }
            results.append(row)
    except Exception as exc:
        logger.exception("Baseline training failed")
        raise HTTPException(status_code=400, detail=f"Could not train the baseline models: {exc}") from exc
    return {
        "task": request.task,
        "target": request.target,
        "features": [column for column in request.features if column not in empty_columns],
        "test_count": len(y_test),
        "train_count": len(y_train),
        "excluded_empty_features": empty_columns,
        "results": results,
        "warning": "Single holdout metrics are preliminary, may be unstable for imbalanced classes, and do not establish generalization.",
    }


@app.post("/api/segments")
def segments(request: ClusterRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    state = workspace_for(x_workspace_id)
    if len(request.columns) < 2 or any(c not in state["data"] for c in request.columns):
        raise HTTPException(status_code=400, detail="Select at least two valid numeric columns.")
    data = state["data"][request.columns].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(data) < 20:
        raise HTTPException(status_code=400, detail="At least 20 complete records are needed.")
    values = StandardScaler().fit_transform(data)
    if request.method == "anomaly":
        model = IsolationForest(contamination=request.contamination, random_state=42, n_estimators=150)
        labels = model.fit_predict(values)
        output = state["data"].loc[data.index].copy()
        output["Anomaly status"] = ["Anomaly" if label == -1 else "Typical" for label in labels]
        output["Anomaly score"] = model.decision_function(values)
        state["analysis"]["anomalies"] = output
        flagged = output[output["Anomaly status"] == "Anomaly"]
        return {"count": len(flagged), "rows": table_rows(flagged, 0, 100), "warning": "Flags are candidates for review, not proof of error or fraud."}
    if request.clusters >= len(data):
        raise HTTPException(status_code=400, detail="Cluster count must be smaller than the number of records.")
    model = KMeans(n_clusters=request.clusters, n_init=10, random_state=42)
    labels = model.fit_predict(values)
    score = float(silhouette_score(values, labels)) if len(data) <= 20_000 and len(set(labels)) > 1 else None
    output = state["data"].loc[data.index].copy()
    output["Segment"] = labels.astype(str)
    summaries = output.groupby("Segment")[request.columns].mean(numeric_only=True).round(2).reset_index().to_dict(orient="records")
    state["analysis"]["segments"] = output
    return {"count": len(data), "score": score, "profiles": summaries, "rows": table_rows(output, 0, 100)}


@app.post("/api/timeseries")
def time_series(request: TimeSeriesRequest, x_workspace_id: str | None = Header(default=None)) -> dict[str, Any]:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    if request.date not in frame or request.value not in frame:
        raise HTTPException(status_code=400, detail="Choose valid date and numeric columns.")
    if request.frequency not in {"D", "W", "MS", "QS", "YS"}:
        raise HTTPException(status_code=400, detail="Choose a supported time frequency.")
    frame = frame[[request.date, request.value]].copy()
    frame[request.date] = pd.to_datetime(frame[request.date], errors="coerce")
    frame[request.value] = pd.to_numeric(frame[request.value], errors="coerce")
    frame = frame.dropna().set_index(request.date).sort_index()
    if frame.empty:
        raise HTTPException(status_code=400, detail="No valid date and measure values were found.")
    aggregate = request.aggregation if request.aggregation in {"mean", "sum", "count", "median"} else "mean"
    result = getattr(frame[request.value].resample(request.frequency), aggregate)().dropna()
    return {"series": [{"name": key.isoformat(), "value": json_value(value)} for key, value in result.items()], "periods": len(result)}


@app.get("/api/export/{kind_name}")
def export_data(kind_name: str, x_workspace_id: str | None = Header(default=None)) -> Response:
    state = workspace_for(x_workspace_id)
    frame = state["data"]
    if kind_name == "csv":
        return Response(frame.to_csv(index=False).encode("utf-8-sig"), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="smart_data_analyst.csv"'})
    if kind_name == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            frame.to_excel(writer, index=False, sheet_name="Cleaned data")
            pd.DataFrame(current_profile(state)["schema"]).to_excel(writer, index=False, sheet_name="Data dictionary")
        return Response(buffer.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="smart_data_analyst.xlsx"'})
    if kind_name == "json":
        data = overview_payload(state)
        return Response(json.dumps(data, default=str).encode(), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="dataset_profile.json"'})
    if kind_name == "pdf":
        return Response(pdf_report(frame, state["name"]), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="analysis_report.pdf"'})
    if kind_name == "segments" and "segments" in state["analysis"]:
        return Response(state["analysis"]["segments"].to_csv(index=False).encode("utf-8-sig"), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="segments.csv"'})
    if kind_name == "anomalies" and "anomalies" in state["analysis"]:
        return Response(state["analysis"]["anomalies"].to_csv(index=False).encode("utf-8-sig"), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="anomaly_review.csv"'})
    raise HTTPException(status_code=404, detail="This export is not available.")


@app.delete("/api/workspace")
def clear_workspace(x_workspace_id: str | None = Header(default=None)) -> dict[str, str]:
    if x_workspace_id:
        workspaces.pop(x_workspace_id, None)
    return {"status": "cleared"}


WEB_DIST = Path(__file__).parent / "web" / "dist"
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
