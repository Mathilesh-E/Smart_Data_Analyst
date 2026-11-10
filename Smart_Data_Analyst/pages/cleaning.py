"""
Page: Smart Cleaning Studio
Non-destructive cleaning workspace: prioritized recommendations,
one-click approval, before-and-after counts, audit trail, and full rollback.
"""
import streamlit as st
import pandas as pd
from smart_analyst.utils import render_hero
from smart_analyst.cleaning import DataCleaningEngine
from smart_analyst.profiler import DataProfiler
from smart_analyst.quality import DataQualityEngine

def render_cleaning_page():
    render_hero(
        title="Smart Data Cleaning Studio",
        subtitle="User-approved, non-destructive data cleaning with instant audit preview and rollback.",
        badge="Non-destructive"
    )

    df_active = st.session_state.get("df_active")
    if df_active is None:
        st.info("Please load or upload a dataset first.")
        return

    quality = st.session_state.get("quality_report", {})
    recs = DataCleaningEngine.get_recommendations(df_active, quality)
    cleaning_log = st.session_state.get("cleaning_log", [])

    c_rst1, c_rst2 = st.columns([1, 4])
    with c_rst1:
        if st.button("🔄 Reset to Original Data", type="secondary"):
            st.session_state["df_active"] = st.session_state["df_raw"].copy()
            st.session_state["cleaning_log"] = []
            st.session_state["is_cleaned"] = False
            st.session_state["profile_report"] = DataProfiler.profile_dataset(st.session_state["df_active"])
            st.session_state["quality_report"] = DataQualityEngine.audit_quality(st.session_state["df_active"])
            st.success("Dataset successfully restored to original raw state.")
            st.rerun()

    st.markdown("### 💡 Prioritized Cleaning Recommendations")
    if not recs:
        st.success("No automated cleaning operations pending. The dataset looks clean!")
    else:
        for idx, rec in enumerate(recs):
            with st.expander(f"🔹 {rec['title']} — [{rec['category']}]", expanded=(idx < 2)):
                st.write(f"**Issue Detected**: {rec['issue']}")
                st.write(f"**Recommended Operation**: {rec['recommendation']}")

                btn_key = f"apply_{rec['id']}_{idx}"
                if st.button(f"Apply: {rec['title']}", key=btn_key, type="primary"):
                    new_df, log_entry = DataCleaningEngine.apply_action(df_active, rec['action'], rec['params'])
                    st.session_state["df_active"] = new_df
                    st.session_state["is_cleaned"] = True
                    cleaning_log.append(log_entry)
                    st.session_state["cleaning_log"] = cleaning_log

                    # Refresh profiles & quality audits
                    st.session_state["profile_report"] = DataProfiler.profile_dataset(new_df)
                    st.session_state["quality_report"] = DataQualityEngine.audit_quality(new_df)
                    st.success(f"Action executed! {log_entry['description']}")
                    st.rerun()

    # Manual Custom Cleaning Tools
    st.markdown("---")
    st.subheader("🛠️ Custom Surgical Cleaning Tools")
    m1, m2 = st.columns(2)

    with m1:
        st.markdown("**Drop Selected Column**")
        col_to_drop = st.selectbox("Select Column to Drop", ["None"] + list(df_active.columns))
        if st.button("Drop Column", type="secondary"):
            if col_to_drop != "None":
                new_df, log = DataCleaningEngine.apply_action(df_active, "drop_column", {"column": col_to_drop})
                st.session_state["df_active"] = new_df
                st.session_state["is_cleaned"] = True
                cleaning_log.append(log)
                st.session_state["cleaning_log"] = cleaning_log
                st.session_state["profile_report"] = DataProfiler.profile_dataset(new_df)
                st.session_state["quality_report"] = DataQualityEngine.audit_quality(new_df)
                st.success(f"Successfully dropped column '{col_to_drop}'.")
                st.rerun()

    with m2:
        st.markdown("**Whitespace & Formatting Normalization**")
        str_cols = list(df_active.select_dtypes(include=["object", "string"]).columns)
        if str_cols:
            sel_str = st.selectbox("Select Text Column", str_cols)
            if st.button("Trim Whitespace & Normalize", type="secondary"):
                new_df, log = DataCleaningEngine.apply_action(df_active, "whitespace_clean", {"column": sel_str})
                st.session_state["df_active"] = new_df
                st.session_state["is_cleaned"] = True
                cleaning_log.append(log)
                st.session_state["cleaning_log"] = cleaning_log
                st.success(f"Normalized text in '{sel_str}'.")
                st.rerun()

    # Cleaning Audit Log
    st.markdown("---")
    st.subheader("📜 Cleaning Operations Audit Trail")
    if cleaning_log:
        st.table(pd.DataFrame(cleaning_log))
    else:
        st.info("No cleaning operations applied yet to this working copy.")

