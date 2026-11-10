"""
Page: 7. Auto Insights
Synthesizes deterministic, rule-based observations, data warnings, and recommendations
derived strictly from empirical statistics.
"""
import streamlit as st
import pandas as pd
from modules.ui_components import render_header
from modules.insight_engine import InsightEngine

def render_auto_insights():
    render_header(
        title="Automated Statistical Insights",
        subtitle="100% offline, explainable observations, risk warnings, and actionable recommendations."
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please upload a dataset first.")
        return

    quality_report = st.session_state.get("quality_report", {})
    profile_report = st.session_state.get("profile_report", {})
    insights = InsightEngine.generate_insights(df, quality_report, profile_report)

    # Filter categories
    cat_filter = st.radio("Filter By Category", ["All", "Observation", "Warning"], horizontal=True)

    filtered_insights = [
        item for item in insights if cat_filter == "All" or item.get("category") == cat_filter
    ]

    st.caption(f"Showing **{len(filtered_insights)}** generated insights.")

    for item in filtered_insights:
        cat = item.get("category", "Observation")
        title = item.get("title", "")
        desc = item.get("description", "")
        metric = item.get("metric", "")
        rec = item.get("recommendation", "")
        cols = item.get("columns", [])

        if cat == "Warning":
            badge_color = "#ef4444"
            bg_color = "rgba(239, 68, 68, 0.08)"
            border_color = "rgba(239, 68, 68, 0.3)"
        else:
            badge_color = "#3b82f6"
            bg_color = "rgba(59, 130, 246, 0.08)"
            border_color = "rgba(59, 130, 246, 0.3)"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{title}</span>
                <span style="background-color: {badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">{cat.upper()}</span>
            </div>
            <div style="font-size: 0.92rem; color: #cbd5e1; margin-bottom: 6px;">{desc}</div>
            <div style="display: flex; gap: 16px; font-size: 0.82rem; color: #94a3b8;">
                <span><b>Supporting Metric:</b> {metric}</span>
                {f"<span><b>Columns:</b> {', '.join(cols)}</span>" if cols else ""}
            </div>
            {f"<div style='margin-top: 8px; padding-top: 6px; border-top: 1px dashed {border_color}; font-size: 0.85rem; color: #38bdf8;'>💡 <b>Action:</b> {rec}</div>" if rec else ""}
        </div>
        """, unsafe_allow_html=True)

