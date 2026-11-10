"""
Page: Reports & Export Hub
Executive ReportLab PDF document compilation, cleaned CSV/Excel downloads,
and full JSON metadata serialization.
"""
import streamlit as st
import pandas as pd
from smart_analyst.utils import render_hero
from smart_analyst.reporting import ReportExporter
from smart_analyst.insights import InsightEngine

def render_reports_page():
    render_hero(
        title="Reports & Data Export Center",
        subtitle="Generate executive ReportLab PDF briefs, export cleaned datasets (CSV/Excel), and download analytical JSON.",
        badge="Export Center"
    )

    df_active = st.session_state.get("df_active")
    if df_active is None:
        st.info("Please load or upload a dataset first.")
        return

    filename = st.session_state.get("dataset_name", "dataset.csv")
    quality = st.session_state.get("quality_report", {})
    profile = st.session_state.get("profile_report", {})
    cleaning_log = st.session_state.get("cleaning_log", [])
    insights = InsightEngine.generate_insights(df_active, quality, profile)

    st.markdown("### 📄 1. Executive Analytics PDF Report")
    st.write("Generate a publication-grade multi-page PDF summary with dynamic page numbering, audit deductions, and automated findings.")

    if st.button("Generate Executive PDF Brief", type="primary"):
        with st.spinner("Compiling ReportLab document..."):
            pdf_bytes = ReportExporter.generate_pdf(
                filename=filename,
                df=df_active,
                quality=quality,
                profile=profile,
                insights=insights,
                cleaning_log=cleaning_log
            )
            st.session_state["pdf_bytes"] = pdf_bytes
            st.success("Executive PDF Brief rendered successfully!")

    if "pdf_bytes" in st.session_state:
        st.download_button(
            label="📥 Download Smart_Data_Analyst_Report.pdf",
            data=st.session_state["pdf_bytes"],
            file_name=f"Smart_Data_Analyst_{filename}.pdf",
            mime="application/pdf"
        )

    st.markdown("---")
    st.markdown("### 💾 2. Cleaned Dataset & Metadata Exports")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Cleaned Dataset (CSV)**")
        csv_bytes = ReportExporter.to_csv_bytes(df_active)
        st.download_button(
            label="📥 Download Cleaned CSV",
            data=csv_bytes,
            file_name=f"Cleaned_{filename}.csv" if not filename.endswith(".csv") else f"Cleaned_{filename}",
            mime="text/csv"
        )

    with c2:
        st.markdown("**Cleaned Dataset (Excel)**")
        excel_bytes = ReportExporter.to_excel_bytes(df_active)
        st.download_button(
            label="📥 Download Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"Cleaned_{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with c3:
        st.markdown("**Data Dictionary & Metrics (JSON)**")
        import json
        json_meta = {
            "dataset_name": filename,
            "quality_audit": quality,
            "profile_summary": profile.get("summary", {}),
            "insights_count": len(insights)
        }
        st.download_button(
            label="📥 Download JSON Metadata",
            data=json.dumps(json_meta, indent=2).encode("utf-8"),
            file_name=f"Metadata_{filename}.json",
            mime="application/json"
        )

