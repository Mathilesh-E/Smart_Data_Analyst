"""
SMART DATA ANALYST
Universal Smart Data Analytics Platform
Main Streamlit Application Controller.
"""
import os
import streamlit as st
import pandas as pd

from smart_analyst.data_loader import DataLoader
from smart_analyst.profiler import DataProfiler
from smart_analyst.quality import DataQualityEngine

# Import domain modules
from pages.overview import render_overview_page
from pages.explorer import render_explorer_page
from pages.quality import render_quality_page
from pages.cleaning import render_cleaning_page
from pages.eda import render_eda_page
from pages.visualization import render_visualization_page
from pages.insights import render_insights_page
from pages.statistical_lab import render_statistical_lab_page
from pages.segmentation import render_segmentation_page
from pages.time_series import render_time_series_page
from pages.ml_lab import render_ml_lab_page
from pages.reports import render_reports_page

st.set_page_config(
    page_title="Smart Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load global custom CSS
css_file = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Session state initialization
def init_session():
    if "df_raw" not in st.session_state:
        st.session_state["df_raw"] = None
    if "df_active" not in st.session_state:
        st.session_state["df_active"] = None
    if "dataset_name" not in st.session_state:
        st.session_state["dataset_name"] = None
    if "profile_report" not in st.session_state:
        st.session_state["profile_report"] = None
    if "quality_report" not in st.session_state:
        st.session_state["quality_report"] = None
    if "cleaning_log" not in st.session_state:
        st.session_state["cleaning_log"] = []
    if "is_cleaned" not in st.session_state:
        st.session_state["is_cleaned"] = False

init_session()

# Sidebar Branding
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
    <span style="font-size: 1.8rem;">📊</span>
    <div>
        <div style="font-size: 1.25rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">Smart Data Analyst</div>
        <div style="font-size: 0.75rem; color: #6366f1; font-weight: 600;">ENTERPRISE ANALYTICS SUITE</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📁 Ingestion Center")

mode = st.sidebar.radio("Data Ingestion Mode", ["Preloaded Benchmarks", "Upload Custom File"], horizontal=True)

if mode == "Preloaded Benchmarks":
    benchmarks = {
        "Retail Sales E-Commerce": "retail_sales.csv",
        "Student Academic Performance": "student_performance.csv",
        "Clinical Healthcare Sample": "healthcare_sample.csv",
        "Airline Flight Delays": "flight_delays.csv"
    }
    sel_b = st.sidebar.selectbox("Choose Benchmark Dataset", list(benchmarks.keys()))
    if st.sidebar.button("Load Selected Benchmark", type="primary"):
        p = os.path.join(os.path.dirname(__file__), "sample_data", benchmarks[sel_b])
        if os.path.exists(p):
            with open(p, "rb") as f:
                b_bytes = f.read()
            df, err = DataLoader.load_dataset(b_bytes, benchmarks[sel_b])
            if df is not None:
                st.session_state["df_raw"] = df.copy()
                st.session_state["df_active"] = df.copy()
                st.session_state["dataset_name"] = benchmarks[sel_b]
                st.session_state["is_cleaned"] = False
                st.session_state["cleaning_log"] = []
                st.session_state["profile_report"] = DataProfiler.profile_dataset(df)
                st.session_state["quality_report"] = DataQualityEngine.audit_quality(df)
                st.sidebar.success(f"Benchmark '{sel_b}' loaded!")
                st.rerun()

else: # Custom upload
    up_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if up_file:
        f_bytes = up_file.getvalue()
        f_name = up_file.name
        sheet = None
        ext = os.path.splitext(f_name)[1].lower()
        if ext in [".xlsx", ".xls"]:
            sheets = DataLoader.get_excel_sheets(f_bytes)
            if len(sheets) > 1:
                sheet = st.sidebar.selectbox("Select Excel Worksheet", sheets)
            elif len(sheets) == 1:
                sheet = sheets[0]

        if st.session_state.get("dataset_name") != f_name:
            with st.spinner("Analyzing uploaded dataset..."):
                df, err = DataLoader.load_dataset(f_bytes, f_name, sheet_name=sheet)
                if err and df is None:
                    st.sidebar.error(err)
                elif df is not None:
                    st.session_state["df_raw"] = df.copy()
                    st.session_state["df_active"] = df.copy()
                    st.session_state["dataset_name"] = f_name
                    st.session_state["is_cleaned"] = False
                    st.session_state["cleaning_log"] = []
                    st.session_state["profile_report"] = DataProfiler.profile_dataset(df)
                    st.session_state["quality_report"] = DataQualityEngine.audit_quality(df)
                    st.sidebar.success(f"Loaded {f_name} ({len(df):,} rows)")
                    st.rerun()

# Navigation
st.sidebar.markdown("---")
st.sidebar.subheader("🧭 Analytics Workspace")

pages_map = {
    "1. Overview Dashboard": render_overview_page,
    "2. Data Explorer": render_explorer_page,
    "3. Data Quality Intelligence": render_quality_page,
    "4. Smart Cleaning Studio": render_cleaning_page,
    "5. EDA Studio": render_eda_page,
    "6. Advanced Visualization": render_visualization_page,
    "7. Automated Insights": render_insights_page,
    "8. Statistical Analysis Lab": render_statistical_lab_page,
    "9. Segmentation & Anomalies": render_segmentation_page,
    "10. Time Series Analytics": render_time_series_page,
    "11. Machine Learning Lab": render_ml_lab_page,
    "12. Reports & Exports": render_reports_page,
}

choice = st.sidebar.radio("Navigate Modules:", list(pages_map.keys()))

# Active dataset badge in sidebar
if st.session_state.get("df_active") is not None:
    st.sidebar.markdown("---")
    st.sidebar.caption("Active Dataset Workspace:")
    st.sidebar.info(
        f"**{st.session_state.get('dataset_name')}**\n\n"
        f"• **{len(st.session_state['df_active']):,}** rows × **{len(st.session_state['df_active'].columns)}** cols\n"
        f"• Status: {'Cleaned Working Copy' if st.session_state.get('is_cleaned') else 'Original Raw Data'}"
    )

# Execute selected module page
pages_map[choice]()
