"""
Page: Automated Insights
Rule-based statistical synthesizer generating observations, warnings,
and data recommendations without external API dependencies.
"""
import streamlit as st
from smart_analyst.utils import render_hero
from smart_analyst.insights import InsightEngine

def render_insights_page():
    render_hero(
        title="Automated Statistical Insights",
        subtitle="100% offline, explainable statistical findings, risk warnings, and actionable recommendations.",
        badge="Zero-API Rules"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    quality = st.session_state.get("quality_report", {})
    profile = st.session_state.get("profile_report", {})
    insights = InsightEngine.generate_insights(df, quality, profile)

    cat_filter = st.radio("Filter Insights by Category", ["All", "observation", "warning"], horizontal=True)
    filtered = [i for i in insights if cat_filter == "All" or i.get("category") == cat_filter]

    st.caption(f"Displaying **{len(filtered)}** generated empirical insights.")

    for item in filtered:
        cat = item.get("category", "observation")
        card_class = "danger" if cat == "danger" else ("warning" if cat == "warning" else "")
        badge_label = cat.upper()
        
        st.markdown(f"""
        <div class="sda-insight-card {card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; font-size: 1.05rem; color: #f8fafc;">{item.get('title')}</span>
                <span class="sda-kpi-badge">{badge_label}</span>
            </div>
            <div style="font-size: 0.92rem; color: #cbd5e1; margin-bottom: 8px;">{item.get('description')}</div>
            <div style="display: flex; gap: 16px; font-size: 0.8rem; color: #94a3b8;">
                <span><b>Metric Evidence:</b> {item.get('metric')}</span>
                {f"<span><b>Variables:</b> {', '.join(item.get('columns'))}</span>" if item.get('columns') else ""}
            </div>
            {f"<div style='margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.84rem; color: #38bdf8;'>💡 <b>Actionable Recommendation:</b> {item.get('recommendation')}</div>" if item.get('recommendation') else ""}
        </div>
        """, unsafe_allow_html=True)

