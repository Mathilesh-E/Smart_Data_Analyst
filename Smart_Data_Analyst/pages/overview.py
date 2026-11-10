"""
Page: Overview Dashboard
Instant executive KPI cards, type classification donut, health audit status,
top observations, and quick preview.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from smart_analyst.utils import render_hero, render_kpi
from smart_analyst.visualization import Visualizer, SDA_PALETTE

def render_overview_page():
    render_hero(
        title="Analytical Executive Overview",
        subtitle="Autonomous structural profiling, health diagnostic index, and dataset composition overview.",
        badge="Autonomous"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("👋 Welcome to **Smart Data Analyst**! Select a benchmark dataset or upload a file from the sidebar to begin.")
        return

    quality = st.session_state.get("quality_report", {})
    profile = st.session_state.get("profile_report", {})
    summary = profile.get("summary", {})
    metrics = quality.get("metrics", {})

    # Top KPI Metrics Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi("Total Records", f"{summary.get('rows', len(df)):,}", f"{summary.get('columns', len(df.columns))} dimensions")
    with col2:
        score = quality.get("score", 0.0)
        color = quality.get("status_color", "#6366f1")
        render_kpi("Health Score", f"{score}/100", f"Grade: {quality.get('status', 'N/A')}", color=color)
    with col3:
        render_kpi("Missing Cells", f"{metrics.get('missing_pct', 0)}%", f"{metrics.get('total_missing', 0):,} cells")
    with col4:
        render_kpi("Duplicate Rows", f"{metrics.get('duplicate_pct', 0)}%", f"{metrics.get('duplicate_rows', 0):,} records")
    with col5:
        render_kpi("Completeness", f"{metrics.get('completeness_pct', 100)}%", "Total observed data")

    st.markdown("---")

    # Layout: Column Type Donut + Health Diagnostic Summary
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("### 🧩 Inferred Column Composition")
        type_counts = summary.get("type_counts", {})
        if type_counts:
            t_df = pd.DataFrame(list(type_counts.items()), columns=["Inferred Type", "Columns"])
            fig = px.pie(t_df, names="Inferred Type", values="Columns", hole=0.55, color_discrete_sequence=SDA_PALETTE)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1"),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 🩺 Diagnostic Health Audit")
        st.markdown(f"""
        - **Data Quality Index**: <span style="color: {quality.get('status_color', '#6366f1')}; font-weight: 700;">{score}/100 ({quality.get('status')})</span>
        - **1.5 × IQR Outliers**: **{metrics.get('total_outliers', 0):,}** extreme values flagged
        - **Constant (0 Variance) Columns**: **{metrics.get('constant_cols_count', 0)}** detected
        - **Working Copy State**: {'Cleaned & Verified' if st.session_state.get('is_cleaned') else 'Original Upload'}
        """, unsafe_allow_html=True)

        if metrics.get("constant_cols"):
            st.caption(f"Zero-variance fields: {', '.join(metrics['constant_cols'])}")

        st.info("💡 **Recommended Next Step**: Visit **Data Quality** or **Smart Cleaning** to inspect issues and apply one-click non-destructive remedies.")

    st.markdown("### 📋 Dataset Instant Snapshot (First 10 Records)")
    st.dataframe(df.head(10), use_container_width=True)
