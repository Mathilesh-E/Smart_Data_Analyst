"""
Page: 2. Data Explorer
Interactive data exploration, multi-criteria filtering (numeric range, categories, search),
sorting, column-specific inspector, and isolated slice preview.
"""
import streamlit as st
import pandas as pd
import numpy as np
from modules.ui_components import render_header

def render_data_explorer():
    render_header(
        title="Interactive Data Explorer",
        subtitle="Dynamic slice-and-dice, multi-column search, categorical filter, and schema inspection."
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset to begin exploration.")
        return

    st.markdown("#### 🔍 Filter & Search")
    with st.expander("Filter Controls (Non-destructive)", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        filtered_df = df.copy()

        with f_col1:
            search_term = st.text_input("Global Search (text columns)", placeholder="Type to filter rows...")
            if search_term:
                text_cols = filtered_df.select_dtypes(include=["object", "string"]).columns
                if len(text_cols) > 0:
                    mask = False
                    for c in text_cols:
                        mask = mask | filtered_df[c].astype(str).str.contains(search_term, case=False, na=False)
                    filtered_df = filtered_df[mask]

        with f_col2:
            num_cols = list(filtered_df.select_dtypes(include=[np.number]).columns)
            if num_cols:
                sel_num_col = st.selectbox("Filter Numeric Column", ["None"] + num_cols)
                if sel_num_col != "None":
                    min_val = float(filtered_df[sel_num_col].min())
                    max_val = float(filtered_df[sel_num_col].max())
                    if min_val < max_val:
                        val_range = st.slider(f"Range for {sel_num_col}", min_val, max_val, (min_val, max_val))
                        filtered_df = filtered_df[
                            (filtered_df[sel_num_col] >= val_range[0]) & (filtered_df[sel_num_col] <= val_range[1])
                        ]

        with f_col3:
            cat_cols = list(filtered_df.select_dtypes(include=["object", "category"]).columns)
            if cat_cols:
                sel_cat_col = st.selectbox("Filter Categorical Column", ["None"] + cat_cols)
                if sel_cat_col != "None":
                    unique_vals = list(filtered_df[sel_cat_col].dropna().unique())[:30]
                    sel_vals = st.multiselect(f"Select values in {sel_cat_col}", unique_vals, default=unique_vals)
                    if sel_vals:
                        filtered_df = filtered_df[filtered_df[sel_cat_col].isin(sel_vals)]

    st.caption(f"Displaying **{len(filtered_df):,}** of **{len(df):,}** records ({round((len(filtered_df)/len(df))*100, 1)}%).")

    # Column selector for display
    all_cols = list(filtered_df.columns)
    selected_cols = st.multiselect("Visible Columns", all_cols, default=all_cols)
    
    st.dataframe(filtered_df[selected_cols], use_container_width=True, height=400)

    # Detailed Column Inspector
    st.markdown("---")
    st.subheader("📋 Deep Column Inspector")
    inspect_col = st.selectbox("Select Column to Inspect", all_cols)
    if inspect_col:
        profile = st.session_state.get("profile_report", {}).get("columns", {}).get(inspect_col, {})
        i_col1, i_col2, i_col3, i_col4 = st.columns(4)
        with i_col1:
            st.metric("Inferred Role", profile.get("type", "Unknown"))
        with i_col2:
            st.metric("Missing Count", f"{profile.get('missing_count', 0)} ({profile.get('missing_pct', 0)}%)")
        with i_col3:
            st.metric("Unique Distinct", profile.get("unique_count", 0))
        with i_col4:
            st.metric("Total Count", profile.get("total_count", 0))

        stats = profile.get("stats", {})
        if stats:
            st.json(stats)

