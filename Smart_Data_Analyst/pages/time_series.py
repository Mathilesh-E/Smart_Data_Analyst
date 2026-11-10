"""
Page: Time Series Analytics
Temporal analysis: automated date column discovery, moving averages,
growth rate indicators, and trend visualizations.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from smart_analyst.utils import render_hero
from smart_analyst.time_series import TimeSeriesEngine
from smart_analyst.visualization import SDA_PALETTE

def render_time_series_page():
    render_hero(
        title="Time Series Analytics",
        subtitle="Chronological trend analysis: multi-frequency resampling, 3-period moving averages, and growth tracking.",
        badge="Temporal Lab"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    # Look for date-like columns
    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or pd.api.types.is_datetime64_any_dtype(df[c])]
    if not date_cols:
        # Fallback to any string or object column
        date_cols = list(df.select_dtypes(include=["object", "string"]).columns)

    num_cols = list(df.select_dtypes(include=[np.number]).columns)

    if not date_cols or not num_cols:
        st.warning("Time series analysis requires at least one date-like column and one numeric metric.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        date_col = st.selectbox("Date / Timestamp Attribute", date_cols)
    with c2:
        val_col = st.selectbox("Numeric Measure Metric", num_cols)
    with c3:
        freq = st.selectbox("Resampling Granularity", ["D (Daily)", "W (Weekly)", "M (Monthly)"], index=1)
        freq_code = freq.split()[0]

    if st.button("Generate Time Series Analysis", type="primary"):
        with st.spinner("Resampling temporal data..."):
            res = TimeSeriesEngine.analyze_series(df, date_col, val_col, freq=freq_code)
            if "error" in res:
                st.error(res["error"])
            else:
                res_df = res["resampled_df"]
                st.success(f"Temporal span: {res['min_date'][:10]} to {res['max_date'][:10]}")

                # Trend chart
                fig = px.line(
                    res_df,
                    x=date_col,
                    y=["mean", "rolling_mean_3"],
                    color_discrete_sequence=[SDA_PALETTE[0], SDA_PALETTE[1]],
                    title=f"Trend & 3-Period Moving Average for {val_col}"
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.4)", font=dict(color="#cbd5e1"))
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### Resampled Time Aggregations Table")
                st.dataframe(res_df, use_container_width=True)

