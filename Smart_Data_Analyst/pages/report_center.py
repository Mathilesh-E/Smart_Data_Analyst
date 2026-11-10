"""
Page: 9. Report Center
Comprehensive export hub: generates multi-page ReportLab PDF reports,
cleaned CSV and Excel (openpyxl) downloads, and JSON metadata packages.
"""
import streamlit as st
import pandas as pd
from modules.ui_components import render_header
from modules.report_generator import ReportGenerator
from modules.export_manager import ExportManager
from modules.insight_engine import InsightEngine

def render_report_center():
    render_header(
        title="Report Center & Data Export Hub",
        subtitle="Generate executive PDF reports, export cleaned datasets (CSV/Excel), and download data profiling JSON."
    )

    df_active = st.session_state.get("df_active")
    if df_active is None:
        st.info("Please upload a dataset first.")
        return

    filename = st.session_state.get("dataset_name", "dataset.csv")
    quality_report = st.session_state.get("quality_report", {})
    profile_report = st.session_state.get("profile_report", {})
    cleaning_log = st.session_state.get("cleaning_log", [])
    ml_results = st.session_state.get("ml_results")
    insights = InsightEngine.generate_insights(df_active, quality_report, profile_report)

    st.markdown("### 📄 1. Executive PDF Analytics Report")
    st.write(
        "Generate a publication-ready PDF summary document containing dataset metrics, "
        "audit score deductions, column profiles, automated observations, and cleaning trails."
    )

    if st.button("Generate Executive PDF Report", type="primary"):
        with st.spinner("Compiling ReportLab document..."):
            pdf_bytes = ReportGenerator.generate_pdf_report(
                filename=filename,
                df=df_active,
                quality_report=quality_report,
                profile_report=profile_report,
                insights=insights,
                cleaning_log=cleaning_log,
                ml_results=ml_results
            )
            st.session_state["pdf_bytes"] = pdf_bytes
            st.success("Executive PDF Report generated successfully!")

    if "pdf_bytes" in st.session_state:
        st.download_button(
            label="📥 Download DataNova_Report.pdf",
            data=st.session_state["pdf_bytes"],
            file_name=f"DataNova_Report_{filename}.pdf",
            mime="application/pdf"
        )

    st.markdown("---")
    st.markdown("### 💾 2. Cleaned Dataset & Metadata Exports")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Cleaned Dataset (CSV)**")
        csv_bytes = ExportManager.to_csv_bytes(df_active)
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv_bytes,
            file_name=f"Cleaned_{filename}.csv" if not filename.endswith(".csv") else f"Cleaned_{filename}",
            mime="text/csv"
        )

    with c2:
        st.markdown("**Cleaned Dataset (Excel)**")
        excel_bytes = ExportManager.to_excel_bytes(df_active)
        st.download_button(
            label="📥 Download Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"Cleaned_{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with c3:
        st.markdown("**Data Profile (JSON)**")
        json_meta = {
            "file_name": filename,
            "quality_audit": quality_report,
            "profile": profile_report,
            "insights": insights
        }
        json_bytes = ExportManager.to_json_bytes(json_meta)
        st.download_button(
            label="📥 Download Metadata JSON",
            data=json_bytes,
            file_name=f"Profile_{filename}.json",
            mime="application/json"
        )

    # Cleaning Log Export
    if cleaning_log:
        st.markdown("---")
        st.markdown("### 📜 3. Cleaning Audit Trail Export")
        log_df = pd.DataFrame(cleaning_log)
        st.download_button(
            label="📥 Download Cleaning Audit Log (CSV)",
            data=ExportManager.to_csv_bytes(log_df),
            file_name=f"Cleaning_Log_{filename}.csv",
            mime="text/csv"
        )

