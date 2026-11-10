"""
Page: Statistical Analysis Lab
Scientific hypothesis testing: Welch's t-test, Mann-Whitney U,
and Chi-Square test of independence with p-values, sample sizes, and effect sizes.
"""
import streamlit as st
import pandas as pd
import numpy as np
from smart_analyst.utils import render_hero
from smart_analyst.statistics import StatisticalLab

def render_statistical_lab_page():
    render_hero(
        title="Statistical Analysis Lab",
        subtitle="Scientific hypothesis testing: Welch's t-test, Mann-Whitney U, and Chi-Square independence tests.",
        badge="Hypothesis Testing"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    cat_cols = list(df.select_dtypes(include=["object", "category", "bool"]).columns)

    test_type = st.selectbox(
        "Select Statistical Hypothesis Test",
        ["Two-Sample Mean Difference (Welch's t-Test)",
         "Two-Sample Rank Difference (Mann-Whitney U Test)",
         "Categorical Association (Chi-Square Test of Independence)"]
    )

    if test_type in ["Two-Sample Mean Difference (Welch's t-Test)", "Two-Sample Rank Difference (Mann-Whitney U Test)"]:
        if not num_cols or not cat_cols:
            st.warning("Two-sample comparison requires at least one numeric measure and one binary/categorical grouping column.")
            return

        c1, c2 = st.columns(2)
        with c1:
            val_col = st.selectbox("Select Numeric Measure", num_cols)
        with c2:
            grp_col = st.selectbox("Select Grouping Attribute (Must have 2 levels)", cat_cols)

        unique_grps = list(df[grp_col].dropna().unique())
        if len(unique_grps) < 2:
            st.warning(f"Grouping column '{grp_col}' must have at least 2 distinct levels.")
            return

        g_sel1, g_sel2 = st.columns(2)
        with g_sel1:
            grp_a = st.selectbox("Group A", unique_grps, index=0)
        with g_sel2:
            grp_b = st.selectbox("Group B", unique_grps, index=min(1, len(unique_grps)-1))

        if grp_a == grp_b:
            st.warning("Please choose two distinct groups.")
            return

        if st.button("Run Hypothesis Test", type="primary"):
            series_a = df[df[grp_col] == grp_a][val_col]
            series_b = df[df[grp_col] == grp_b][val_col]

            if test_type.startswith("Two-Sample Mean"):
                res = StatisticalLab.run_two_sample_ttest(series_a, series_b)
            else:
                res = StatisticalLab.run_mann_whitney(series_a, series_b)

            if "error" in res:
                st.error(res["error"])
            else:
                st.success(f"Hypothesis Test Completed: **{res['test']}**")
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    st.metric(res["stat_name"], res["stat_value"])
                with r2:
                    st.metric("p-value", f"{res['p_value']:.4e}")
                with r3:
                    st.metric("Sample Sizes (A / B)", f"{res['sample_size_a']} / {res['sample_size_b']}")
                with r4:
                    sig_label = "Statistically Significant (p < 0.05)" if res["significant_at_05"] else "Not Significant (p >= 0.05)"
                    st.metric("Conclusion (α=0.05)", sig_label)

    else: # Chi-square
        if len(cat_cols) < 2:
            st.warning("Chi-square test of independence requires at least 2 categorical attributes.")
            return

        c1, c2 = st.columns(2)
        with c1:
            cat_a = st.selectbox("Categorical Attribute A", cat_cols, index=0)
        with c2:
            cat_b = st.selectbox("Categorical Attribute B", cat_cols, index=1)

        if cat_a == cat_b:
            st.warning("Please select two distinct categorical columns.")
            return

        if st.button("Run Chi-Square Test", type="primary"):
            res = StatisticalLab.run_chi_square(df, cat_a, cat_b)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success("Chi-Square Test of Independence Executed")
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.metric("Chi2 Statistic", res["stat_value"])
                with r2:
                    st.metric("p-value", f"{res['p_value']:.4e}")
                with r3:
                    st.metric("Cramér's V (Effect Size)", res["cramers_v"])

                st.markdown("#### Observed Contingency Cross-Tabulation")
                st.dataframe(res["contingency_table"], use_container_width=True)

