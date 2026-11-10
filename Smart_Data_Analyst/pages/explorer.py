"""
Page: Data Explorer
Interactive data table with multi-column filtering, search, sorting,
and column data dictionary inspector.
"""
import streamlit as st
import pandas as pd
import numpy as np
from smart_analyst.utils import render_hero

def render_explorer_page():
    render_hero(
        title="Interactive Data Explorer",
        subtitle="Dynamic slice-and-dice, global keyword search, numeric range sliders, and column metadata.",
        badge="Interactive"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset to begin exploration.")
        return

    st.markdown("#### 🔍 Multi-Criteria Filter Controls")
    with st.expander("Filter & Search Controls (Non-destructive)", expanded=True):
        c1, c2, c3 = st.columns(3)
        filtered_df = df.copy()

        with c1:
            query = st.text_input("Global Keyword Search", placeholder="Filter records across text columns...")
            if query:
                str_cols = filtered_df.select_dtypes(include=["object", "string"]).columns
                if len(str_cols) > 0:
                    mask = False
                    for col in str_cols:
                        mask = mask | filtered_df[col].astype(str).str.contains(query, case=False, na=False)
                    filtered_df = filtered_df[mask]

        with c2:
            num_cols = list(filtered_df.select_dtypes(include=[np.number]).columns)
            if num_cols:
                sel_num = st.selectbox("Filter Numeric Attribute", ["None"] + num_cols)
                if sel_num != "None":
                    min_v = float(filtered_df[sel_num].min())
                    max_v = float(filtered_df[sel_num].max())
                    if min_v < max_v:
                        rng = st.slider(f"Range for {sel_num}", min_v, max_v, (min_v, max_v))
                        filtered_df = filtered_df[(filtered_df[sel_num] >= rng[0]) & (filtered_df[sel_num] <= rng[1])]

        with c3:
            cat_cols = list(filtered_df.select_dtypes(include=["object", "category"]).columns)
            if cat_cols:
                sel_cat = st.selectbox("Filter Categorical Attribute", ["None"] + cat_cols)
                if sel_cat != "None":
                    uniques = list(filtered_df[sel_cat].dropna().unique())[:30]
                    chosen = st.multiselect(f"Select values in {sel_cat}", uniques, default=uniques)
                    if chosen:
                        filtered_df = filtered_df[filtered_df[sel_cat].isin(chosen)]

    st.caption(f"Displaying **{len(filtered_df):,}** of **{len(df):,}** records ({round((len(filtered_df)/len(df))*100, 1)}%).")

    # Column selector
    all_cols = list(filtered_df.columns)
    visible_cols = st.multiselect("Visible Columns", all_cols, default=all_cols)
    st.dataframe(filtered_df[visible_cols], use_container_width=True, height=380)

    # Deep Column Profile Inspector
    st.markdown("---")
    st.subheader("📋 Deep Column Data Dictionary")
    ins_col = st.selectbox("Inspect Attribute Metadata", all_cols)
    if ins_col:
        col_prof = st.session_state.get("profile_report", {}).get("columns", {}).get(ins_col, {})
        i1, i2, i3, i4 = st.columns(4)
        with i1:
            st.metric("Inferred Type", col_prof.get("type", "Unknown"))
        with i2:
            st.metric("Missing Count", f"{col_prof.get('missing_count', 0)} ({col_prof.get('missing_pct', 0)}%)")
        with i3:
            st.metric("Distinct Uniques", col_prof.get("unique_count", 0))
        with i4:
            st.metric("Total Count", col_prof.get("total_count", 0))

        stats = col_prof.get("stats", {})
        if stats:
            st.json(stats)

