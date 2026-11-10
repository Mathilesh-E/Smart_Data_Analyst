"""
Page: 3. Data Quality
Comprehensive audit of missingness, duplicate rows, zero-variance columns,
1.5*IQR outliers, and formula-backed score explanation.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.ui_components import render_header, render_kpi

def render_data_quality():
    render_header(
        title="Data Quality Intelligence",
        subtitle="Transparent data-quality audit, deduction breakdown, and anomaly detection."
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please upload a dataset to perform quality auditing.")
        return

    quality_report = st.session_state.get("quality_report", {})
    score = quality_report.get("score", 0.0)
    status = quality_report.get("status", "N/A")
    status_color = quality_report.get("status_color", "#3b82f6")
    metrics = quality_report.get("metrics", {})
    deductions = quality_report.get("deductions", {})

    # Top KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi("Quality Score", f"{score} / 100", f"Grade: {status}", delta_color=status_color)
    with col2:
        render_kpi("Missing Cells", f"{metrics.get('missing_pct', 0)}%", f"{metrics.get('total_missing', 0):,} cells")
    with col3:
        render_kpi("Duplicate Rows", f"{metrics.get('duplicate_pct', 0)}%", f"{metrics.get('duplicate_rows', 0):,} records")
    with col4:
        render_kpi("Detected Outliers", f"{metrics.get('total_outliers', 0):,}", "IQR 1.5x rule")

    st.markdown("---")

    # Quality Formula & Deductions Breakdown
    st.subheader("Transparent Score Calculation")
    st.markdown("""
    The **DataNova Quality Score (Q)** is an objective metric calculated from 4 verified vectors:  
    $$\\mathbf{Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)}$$
    Where **M** = % Missing Cells, **D** = % Duplicate Rows, **C** = % Constant Columns, and **I** = % Invalid/Empty Cells.
    """)

    deduct_df = pd.DataFrame([
        {"Vector": "Missing Values (M)", "Observed": f"{metrics.get('missing_pct', 0)}%", "Weight": "50%", "Penalty": f"-{deductions.get('missing_deduction', 0)} pts"},
        {"Vector": "Duplicate Rows (D)", "Observed": f"{metrics.get('duplicate_pct', 0)}%", "Weight": "25%", "Penalty": f"-{deductions.get('duplicate_deduction', 0)} pts"},
        {"Vector": "Constant Columns (C)", "Observed": f"{metrics.get('constant_cols_count', 0)} cols", "Weight": "15%", "Penalty": f"-{deductions.get('constant_deduction', 0)} pts"},
        {"Vector": "Invalid / Empty Cells (I)", "Observed": f"{metrics.get('infinite_values', 0)} inf / {len(metrics.get('empty_cols', []))} empty", "Weight": "10%", "Penalty": f"-{deductions.get('invalid_deduction', 0)} pts"}
    ])
    st.table(deduct_df)

    # Missing Value Heatmap / Bar
    st.markdown("---")
    st.subheader("Missing Value Distribution per Column")
    missing_series = df.isna().sum()
    missing_series = missing_series[missing_series > 0].sort_values(ascending=False)
    
    if len(missing_series) > 0:
        miss_df = pd.DataFrame({
            "Column": missing_series.index,
            "Missing Count": missing_series.values,
            "Missing Pct": ((missing_series.values / len(df)) * 100).round(2)
        })
        fig = px.bar(
            miss_df,
            x="Column",
            y="Missing Pct",
            text="Missing Count",
            color="Missing Pct",
            color_continuous_scale="Reds",
            title="Columns Ranked by Missing Rate (%)"
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("🎉 Excellent! Zero missing values detected across the dataset.")

    # Outlier Details
    st.markdown("---")
    st.subheader("Statistical Outlier Analysis (1.5 × IQR)")
    outlier_info = metrics.get("outlier_info", {})
    if outlier_info:
        out_rows = []
        for col, data in outlier_info.items():
            out_rows.append({
                "Column": col,
                "Outlier Count": data["count"],
                "Outlier %": f"{data['pct']}%",
                "Lower Bound": data["lower_bound"],
                "Upper Bound": data["upper_bound"]
            })
        st.dataframe(pd.DataFrame(out_rows), use_container_width=True)
    else:
        st.info("No extreme numerical outliers detected outside 1.5*IQR bounds.")

