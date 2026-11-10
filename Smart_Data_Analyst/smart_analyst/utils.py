"""
Smart Data Analyst UI Components
Glassmorphism cards, hero banners, and KPI grids.
"""
import streamlit as st

def render_hero(title: str, subtitle: str, badge: str = "Enterprise Engine"):
    st.markdown(f"""
    <div class="sda-header-hero">
        <div class="sda-title">
            <span>{title}</span>
            <span class="sda-kpi-badge">{badge}</span>
        </div>
        <div class="sda-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi(label: str, value: str, subtext: str = "", badge: str = None, color: str = None):
    color_style = f"style='color: {color};'" if color else ""
    badge_html = f"<span class='sda-kpi-badge'>{badge}</span>" if badge else ""
    st.markdown(f"""
    <div class="sda-kpi-card">
        <div class="sda-kpi-label">
            <span>{label}</span>
            {badge_html}
        </div>
        <div class="sda-kpi-val" {color_style}>{value}</div>
        <div class="sda-kpi-sub">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

