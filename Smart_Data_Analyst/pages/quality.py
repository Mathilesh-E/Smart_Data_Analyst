"""
Page: Data Quality
Audit engine displaying formula-backed Data Quality Index, deduction breakdown,
missing value rank chart, and 1.5*IQR outlier tables.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from smart_analyst.utils import render_hero, render_kpi

def render_quality_page():
    render_hero(
        title="Data Quality Intelligence",
        subtitle="Transparent 4-vector quality formula, deduction accounting, and anomaly diagnostics.",
        badge="Audited"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    quality = st.session_state.get("quality_report", {})
    score = quality.get("score", 0.0)
    status = quality.get("status", "N/A")
    status_color = quality.get("status_color", "#6366f1")
    metrics = quality.get("metrics", {})
    deductions = quality.get("deductions", {})

    # Top KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi("Quality Score", f"{score} / 100", f"Grade: {status}", color=status_color)
    with col2:
        render_kpi("Missing Cells", f"{metrics.get('missing_pct', 0)}%", f"{metrics.get('total_missing', 0):,} cells")
    with col3:
        render_kpi("Duplicate Rows", f"{metrics.get('duplicate_pct', 0)}%", f"{metrics.get('duplicate_rows', 0):,} records")
    with col4:
        render_kpi("Detected Outliers", f"{metrics.get('total_outliers', 0):,}", "1.5 × IQR rule")

    st.markdown("---")

    # Formula breakdown table
    st.markdown("### 🧮 Explainable Data Quality Score Formula")
    st.markdown("""
    The **Data Quality Index (Q)** is an objective metric calculated from 4 verified vectors:  
    $$\\mathbf{Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)}$$
    Where **M** = % Missing Cells, **D** = % Duplicate Rows, **C** = % Constant Columns, and **I** = % Invalid/Empty Cells.
    """)

    ded_df = pd.DataFrame([
        {"Vector": "Missing Values (M)", "Observed": f"{metrics.get('missing_pct', 0)}%", "Weight": "50%", "Penalty": f"-{deductions.get('missing', 0)} pts"},
        {"Vector": "Duplicate Rows (D)", "Observed": f"{metrics.get('duplicate_pct', 0)}%", "Weight": "25%", "Penalty": f"-{deductions.get('duplicates', 0)} pts"},
        {"Vector": "Constant Columns (C)", "Observed": f"{metrics.get('constant_cols_count', 0)} cols", "Weight": "15%", "Penalty": f"-{deductions.get('constant', 0)} pts"},
        {"Vector": "Invalid / Empty Cells (I)", "Observed": f"{metrics.get('infinite_values', 0)} inf / {len(metrics.get('empty_cols', []))} empty", "Weight": "10%", "Penalty": f"-{deductions.get('invalid', 0)} pts"}
    ])
    st.table(ded_df)

    # Missing Value Ranking Chart
    st.markdown("---")
    st.markdown("### 📉 Missing Values per Attribute")
    miss_series = df.isna().sum()
    miss_series = miss_series[miss_series > 0].sort_values(ascending=False)

    if len(miss_series) > 0:
        m_df = pd.DataFrame({
            "Column": miss_series.index,
            "Missing Count": miss_series.values,
            "Missing %": ((miss_series.values / len(df)) * 100).round(2)
        })
        fig = px.bar(
            m_df,
            x="Column",
            y="Missing %",
            text="Missing Count",
            color="Missing %",
            color_continuous_scale="Reds",
            title="Columns Ranked by Missing Rate (%)"
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.4)", font=dict(color="#cbd5e1"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("🎉 Outstanding! Zero missing values detected across all attributes.")

    # Outlier Table
    st.markdown("---")
    st.markdown("### ⚠️ Statistical Outliers (1.5 × IQR)")
    out_info = metrics.get("outlier_info", {})
    if out_info:
        rows = []
        for col, data in out_info.items():
            rows.append({
                "Column": col,
                "Outliers Count": data["count"],
                "Outliers %": f"{data['pct']}%",
                "Lower Fence": data["lower_bound"],
                "Upper Fence": data["upper_bound"]
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No extreme numerical outliers detected outside 1.5*IQR bounds.")

