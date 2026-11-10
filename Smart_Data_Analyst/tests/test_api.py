from io import BytesIO

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import app, read_upload

client = TestClient(app)


def test_csv_upload_profiles_and_exports():
    response = client.post(
        "/api/upload",
        files={"file": ("sample.csv", b"score,group\n1.5,A\n2.5,B\n3.5,A\n", "text/csv")},
    )
    assert response.status_code == 200
    result = response.json()
    workspace = result["workspace_id"]
    headers = {"X-Workspace-Id": workspace}
    assert result["overview"]["profile"]["rows"] == 3
    assert result["overview"]["profile"]["numeric"] == ["score"]
    assert client.get("/api/table", headers=headers).json()["total"] == 3
    export = client.get("/api/export/csv", headers=headers)
    assert export.status_code == 200
    assert b"score,group" in export.content


def test_upload_encoding_and_duplicate_headers():
    frame = read_upload("name,name,\nAndré,one,blank\nBéa,two,blank\n".encode("latin-1"), "labels.csv")
    assert len(set(frame.columns)) == 3
    assert frame.iloc[0, 0] == "André"
    assert frame.iloc[1, 0] == "Béa"


def test_empty_headers_are_named_and_invalid_numeric_values_are_reported():
    frame = read_upload(b",score\nrow,1\n", "headers.csv")
    assert frame.columns[0] == "unnamed_1"

    rows = ["score"] + [str(value) for value in range(300)] + ["not-a-number"]
    response = client.post(
        "/api/upload",
        files={"file": ("invalid.csv", "\n".join(rows).encode(), "text/csv")},
    )
    overview = response.json()["overview"]
    assert overview["invalid_values"] == 1
    assert overview["profile"]["missing"] == 1
    assert overview["profile"]["schema"][0]["Invalid values"] == 1


def test_infinite_numeric_values_are_reported_and_normalized():
    response = client.post(
        "/api/upload",
        files={"file": ("infinite.csv", b"score\n1\n2\ninf\n4\n", "text/csv")},
    )
    overview = response.json()["overview"]
    assert overview["invalid_values"] == 1
    diagnostic = next(row for row in overview["diagnostics"] if row["Column"] == "score")
    assert diagnostic["Infinite values"] == 0
    assert diagnostic["Missing"] == 1


def test_excel_upload():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"value": [1, 2], "category": ["a", "b"]}).to_excel(writer, index=False)
    frame = read_upload(buffer.getvalue(), "sample.xlsx")
    assert frame.shape == (2, 2)


def test_empty_csv_is_rejected():
    with pytest.raises(HTTPException) as error:
        read_upload(b"column\n", "empty.csv")
    assert "no data rows" in error.value.detail


def test_cleaning_preview_apply_and_original_reset():
    response = client.post(
        "/api/upload",
        files={"file": ("missing.csv", b"age,city\n10,A\n,B\n30,A\n", "text/csv")},
    )
    workspace = response.json()["workspace_id"]
    headers = {"X-Workspace-Id": workspace}
    action = {"actions": [{"key": "missing:age", "strategy": "median"}]}
    preview = client.post("/api/cleaning/preview", headers=headers, json=action)
    assert preview.status_code == 200
    assert preview.json()["after"]["rows"] == 3
    applied = client.post("/api/cleaning/apply", headers=headers, json=action)
    assert applied.status_code == 200
    assert applied.json()["profile"]["missing"] == 0
    reset = client.post("/api/reset", headers=headers)
    assert reset.json()["profile"]["missing"] == 1


def test_bad_file_type_returns_clear_error():
    response = client.post(
        "/api/upload",
        files={"file": ("readme.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 415
    assert "CSV" in response.json()["detail"]


def test_all_four_sample_datasets_load_with_distinct_profiles():
    samples = client.get("/api/samples").json()
    assert len(samples) == 4
    profiles = []
    for sample in samples:
        response = client.post(f"/api/samples/{sample['file']}")
        assert response.status_code == 200
        profiles.append(response.json()["overview"]["profile"])
    assert all(profile["rows"] > 0 for profile in profiles)
    assert len({tuple(profile["schema"][0]["Column"] for _ in [0]) for profile in profiles}) > 1


def test_chi_square_test_returns_effect_size():
    rows = ["left,right"] + [
        f"{'A' if index % 2 else 'B'},{'X' if index % 3 else 'Y'}"
        for index in range(60)
    ]
    upload = client.post(
        "/api/upload",
        files={"file": ("categories.csv", "\n".join(rows).encode(), "text/csv")},
    )
    headers = {"X-Workspace-Id": upload.json()["workspace_id"]}
    result = client.post(
        "/api/statistics",
        headers=headers,
        json={"test": "chi_square", "x": "left", "group": "right"},
    )
    assert result.status_code == 200
    assert result.json()["n"] == 60
    assert 0 <= result.json()["effect"] <= 1


def test_chart_api_supports_correlation_scatter_and_donut():
    loaded = client.post("/api/samples/retail_sales.csv").json()
    headers = {"X-Workspace-Id": loaded["workspace_id"]}
    correlation = client.post("/api/chart", headers=headers, json={"chart": "correlation"})
    assert correlation.status_code == 200
    assert len(correlation.json()["columns"]) > 1
    scatter = client.post(
        "/api/chart",
        headers=headers,
        json={"chart": "scatter", "x": "units", "y": "revenue"},
    )
    assert scatter.status_code == 200
    assert scatter.json()["series"]
    donut = client.post(
        "/api/chart",
        headers=headers,
        json={"chart": "pie", "x": "region"},
    )
    assert donut.status_code == 200
    assert donut.json()["series"]


def test_analysis_workbench_supports_type_aware_and_grouped_operations():
    loaded = client.post("/api/samples/retail_sales.csv").json()
    headers = {"X-Workspace-Id": loaded["workspace_id"]}
    grouped = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "group_summary", "columns": ["revenue", "units"], "group_by": "region", "statistic": "mean"},
    )
    assert grouped.status_code == 200
    assert grouped.json()["rows"]
    assert grouped.json()["columns"] == ["Group", "revenue", "units"]

    correlation = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "correlation", "columns": ["units", "unit_price", "revenue"], "method": "spearman"},
    )
    assert correlation.status_code == 200
    assert len(correlation.json()["matrix"]) == 3
    assert len(correlation.json()["pair_counts"]) == 3

    crosstab = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "crosstab", "columns": ["region", "category"]},
    )
    assert crosstab.status_code == 200
    assert crosstab.json()["rows"]

    pivot = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "pivot_table", "columns": ["revenue"], "group_by": "region", "column_by": "category", "statistic": "sum"},
    )
    assert pivot.status_code == 200
    assert pivot.json()["rows"]
    assert "revenue" in pivot.json()["title"]
    assert len(pivot.json()["columns"]) > 2

    frequency = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "frequency", "columns": ["region"]},
    )
    assert frequency.status_code == 200
    assert sum(row["Count"] for row in frequency.json()["rows"]) == 360


def test_analysis_missing_outlier_duplicate_and_controls_endpoints():
    upload = client.post(
        "/api/upload",
        files={"file": ("audit.csv", b"group,value\nA,1\nA,2\nA,3\nB,4\nB,5\nB,6\nB,7\nB,100\nB,100\nC,\n", "text/csv")},
    )
    headers = {"X-Workspace-Id": upload.json()["workspace_id"]}
    controls = client.get("/api/controls", headers=headers)
    assert controls.status_code == 200
    assert {item["column"] for item in controls.json()["columns"]} == {"group", "value"}
    assert next(item for item in controls.json()["columns"] if item["column"] == "group")["options"]

    missing = client.post("/api/analysis", headers=headers, json={"operation": "missingness"})
    assert missing.json()["rows_with_missing"] == 1
    outliers = client.post(
        "/api/analysis",
        headers=headers,
        json={"operation": "outliers", "columns": ["value"], "method": "iqr"},
    )
    assert outliers.status_code == 200
    assert outliers.json()["rows"][0]["Potential outliers"] >= 1
    duplicates = client.post("/api/analysis", headers=headers, json={"operation": "duplicates"})
    assert duplicates.json()["duplicate_rows"] == 1


def test_chart_slicers_and_grouped_series_are_applied_before_aggregation():
    loaded = client.post("/api/samples/retail_sales.csv").json()
    headers = {"X-Workspace-Id": loaded["workspace_id"]}
    grouped = client.post(
        "/api/chart",
        headers=headers,
        json={
            "chart": "grouped_bar",
            "x": "region",
            "y": "revenue",
            "color": "category",
            "aggregation": "mean",
            "filters": [{"column": "region", "operator": "eq", "value": "East"}],
        },
    )
    assert grouped.status_code == 200
    assert grouped.json()["records_after_filters"] < grouped.json()["records_before_filters"]
    assert grouped.json()["series_names"]
    assert grouped.json()["series"]
    assert all(row["name"] == "East" for row in grouped.json()["series"])

    between = client.post(
        "/api/chart",
        headers=headers,
        json={
            "chart": "histogram",
            "x": "units",
            "filters": [{"column": "units", "operator": "between", "value": 2, "value_to": 3}],
        },
    )
    assert between.status_code == 200
    assert between.json()["records_after_filters"] > 0


def test_chart_filter_rejects_unknown_slicer_column():
    loaded = client.post("/api/samples/retail_sales.csv").json()
    response = client.post(
        "/api/chart",
        headers={"X-Workspace-Id": loaded["workspace_id"]},
        json={"chart": "category", "x": "region", "filters": [{"column": "missing", "value": "x"}]},
    )
    assert response.status_code == 400
    assert "Unknown filter column" in response.json()["detail"]


def test_date_slicer_matches_a_full_day():
    loaded = client.post("/api/samples/retail_sales.csv").json()
    headers = {"X-Workspace-Id": loaded["workspace_id"]}
    response = client.post(
        "/api/chart",
        headers=headers,
        json={
            "chart": "category",
            "x": "region",
            "filters": [{"column": "order_date", "operator": "eq", "value": "2025-01-01"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["records_after_filters"] == 1


def test_numeric_equality_slicer_matches_integer_input_to_float_column():
    upload = client.post(
        "/api/upload",
        files={"file": ("numeric-filter.csv", b"group,value\nA,1.0\nB,2.0\nC,1.0\n", "text/csv")},
    )
    response = client.post(
        "/api/chart",
        headers={"X-Workspace-Id": upload.json()["workspace_id"]},
        json={"chart": "category", "x": "group", "filters": [{"column": "value", "operator": "eq", "value": "1"}]},
    )
    assert response.status_code == 200
    assert response.json()["records_after_filters"] == 2


def test_group_summary_rejects_using_the_group_as_its_only_measure():
    upload = client.post(
        "/api/upload",
        files={"file": ("grouping.csv", b"value\n1\n2\n3\n", "text/csv")},
    )
    response = client.post(
        "/api/analysis",
        headers={"X-Workspace-Id": upload.json()["workspace_id"]},
        json={"operation": "group_summary", "columns": ["value"], "group_by": "value"},
    )
    assert response.status_code == 400
    assert "different from the grouping column" in response.json()["detail"]



def test_classification_baselines_run_on_user_selected_features():
    rows = ["target,signal,group"]
    for index in range(100):
        target = index % 2
        rows.append(f"{target},{target * 4 + index % 7},{'east' if index % 3 else 'west'}")
    upload = client.post(
        "/api/upload",
        files={"file": ("model.csv", "\n".join(rows).encode(), "text/csv")},
    )
    headers = {"X-Workspace-Id": upload.json()["workspace_id"]}
    result = client.post(
        "/api/ml",
        headers=headers,
        json={"task": "classification", "target": "target", "features": ["signal", "group"]},
    )
    assert result.status_code == 200
    assert result.json()["test_count"] == 20
    assert len(result.json()["results"]) == 2
    assert "accuracy" in result.json()["results"][0]


def test_regression_baselines_run():
    rows = ["target,signal,group"]
    for index in range(60):
        rows.append(f"{index * 1.7 + index % 5},{index},{'north' if index % 2 else 'south'}")
    upload = client.post(
        "/api/upload",
        files={"file": ("regression.csv", "\n".join(rows).encode(), "text/csv")},
    )
    headers = {"X-Workspace-Id": upload.json()["workspace_id"]}
    result = client.post(
        "/api/ml",
        headers=headers,
        json={"task": "regression", "target": "target", "features": ["signal", "group"]},
    )
    assert result.status_code == 200
    assert len(result.json()["results"]) == 2
    assert "rmse" in result.json()["results"][0]


def test_time_series_segments_and_pdf_exports():
    loaded = client.post("/api/samples/flight_delays.csv").json()
    headers = {"X-Workspace-Id": loaded["workspace_id"]}
    time_result = client.post(
        "/api/timeseries",
        headers=headers,
        json={"date": "flight_date", "value": "delay_minutes", "frequency": "D"},
    )
    assert time_result.status_code == 200
    assert time_result.json()["periods"] > 1
    clusters = client.post(
        "/api/segments",
        headers=headers,
        json={"columns": ["delay_minutes", "distance_km"], "clusters": 3},
    )
    assert clusters.status_code == 200
    assert clusters.json()["count"] == 30
    assert client.get("/api/export/pdf", headers=headers).content.startswith(b"%PDF")
    anomalies = client.post(
        "/api/segments",
        headers=headers,
        json={"columns": ["delay_minutes", "distance_km"], "method": "anomaly"},
    )
    assert anomalies.status_code == 200
    assert anomalies.json()["count"] > 0
    assert client.get("/api/export/anomalies", headers=headers).status_code == 200


def test_pdf_export_escapes_uploaded_names_and_values():
    response = client.post(
        "/api/upload",
        files={"file": ("report & <review>.csv", b"category,value\n<urgent>,1\nnormal,2\n", "text/csv")},
    )
    headers = {"X-Workspace-Id": response.json()["workspace_id"]}
    report = client.get("/api/export/pdf", headers=headers)
    assert report.status_code == 200
    assert report.content.startswith(b"%PDF")
