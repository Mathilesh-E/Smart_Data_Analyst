"""
Page: 4. Smart Cleaning
Interactive, user-approved data cleaning.
Non-destructive: original upload is untouched.
Generates operation previews, maintains audit log, and supports full undo/reset.
"""
import streamlit as st
import pandas as pd
from modules.ui_components import render_header
from modules.data_cleaner import DataCleaner
from modules.data_profiler import DataProfiler
from modules.data_quality import DataQualityEngine

def render_smart_cleaning():
    render_header(
        title="Smart Data Cleaning Studio",
        subtitle="User-controlled, non-destructive data cleaning with instant before/after preview."
    )

    df_active = st.session_state.get("df_active")
    if df_active is None:
        st.info("Please upload a dataset first.")
        return

    quality_report = st.session_state.get("quality_report", {})
    recs = DataCleaner.generate_recommendations(df_active, quality_report)
    cleaning_log = st.session_state.get("cleaning_log", [])

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🔄 Reset to Original Data", type="secondary"):
            st.session_state["df_active"] = st.session_state["df_raw"].copy()
            st.session_state["cleaning_log"] = []
            st.session_state["is_cleaned"] = False
            # Recompute audit
            st.session_state["profile_report"] = DataProfiler.profile_dataset(st.session_state["df_active"])
            st.session_state["quality_report"] = DataQualityEngine.audit_quality(st.session_state["df_active"])
            st.success("Dataset successfully reset to original state.")
            st.rerun()

    st.markdown("### 💡 Recommended Cleaning Actions")
    if not recs:
        st.success("No automated cleaning operations pending. The dataset looks clean!")
    else:
        for idx, rec in enumerate(recs):
            with st.expander(f"🔹 {rec['title']} — [{rec['category']}]", expanded=(idx < 2)):
                st.write(f"**Issue**: {rec['issue']}")
                st.write(f"**Recommendation**: {rec['recommendation']}")
                
                # Interactive preview & execution
                btn_key = f"apply_{rec['id']}_{idx}"
                if st.button(f"Apply: {rec['title']}", key=btn_key, type="primary"):
                    new_df, log_entry = DataCleaner.apply_action(df_active, rec['action_type'], rec['params'])
                    st.session_state["df_active"] = new_df
                    st.session_state["is_cleaned"] = True
                    cleaning_log.append(log_entry)
                    st.session_state["cleaning_log"] = cleaning_log
                    
                    # Refresh profile & quality audit
                    st.session_state["profile_report"] = DataProfiler.profile_dataset(new_df)
                    st.session_state["quality_report"] = DataQualityEngine.audit_quality(new_df)
                    
                    st.success(f"Action executed! {log_entry['details']}")
                    st.rerun()

    # Manual Custom Cleaning Tools
    st.markdown("---")
    st.subheader("🛠️ Manual Cleaning Tools")
    m_col1, m_col2 = st.columns(2)
    
    with m_col1:
        st.markdown("**Drop Selected Column**")
        col_to_drop = st.selectbox("Select Column to Drop", ["None"] + list(df_active.columns))
        if st.button("Drop Column", type="secondary"):
            if col_to_drop != "None":
                new_df, log = DataCleaner.apply_action(df_active, "drop_column", {"column": col_to_drop})
                st.session_state["df_active"] = new_df
                st.session_state["is_cleaned"] = True
                cleaning_log.append(log)
                st.session_state["cleaning_log"] = cleaning_log
                st.session_state["profile_report"] = DataProfiler.profile_dataset(new_df)
                st.session_state["quality_report"] = DataQualityEngine.audit_quality(new_df)
                st.success(f"Dropped column {col_to_drop}")
                st.rerun()

    with m_col2:
        st.markdown("**Text Normalization (Trim & Case)**")
        text_cols = list(df_active.select_dtypes(include=["object", "string"]).columns)
        if text_cols:
            sel_text_col = st.selectbox("Select Text Column", text_cols)
            case_opt = st.selectbox("Capitalization", ["Keep Case", "lower", "title"])
            if st.button("Normalize Text", type="secondary"):
                new_df, log = DataCleaner.apply_action(
                    df_active, "text_normalize", {"column": sel_text_col, "case": case_opt.lower()}
                )
                st.session_state["df_active"] = new_df
                st.session_state["is_cleaned"] = True
                cleaning_log.append(log)
                st.session_state["cleaning_log"] = cleaning_log
                st.success(f"Normalized text in {sel_text_col}")
                st.rerun()

    # Cleaning History Audit Log
    st.markdown("---")
    st.subheader("📜 Cleaning Audit Trail")
    if cleaning_log:
        st.table(pd.DataFrame(cleaning_log))
    else:
        st.info("No cleaning operations applied yet to this working copy.")

