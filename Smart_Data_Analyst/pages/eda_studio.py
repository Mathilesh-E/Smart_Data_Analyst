"""
Page: 5. EDA Studio
Exploratory Data Analysis: descriptive statistics, distribution metrics,
pairwise correlations (Pearson/Spearman), and group aggregations.
"""
import streamlit as st
import pandas as pd
import numpy as np
from modules.ui_components import render_header
from modules.eda_engine import EDAEngine
from modules.visualization import Visualizer

def render_eda_studio():
    render_header(
        title="Exploratory Data Analysis (EDA) Studio",
        subtitle="In-depth statistical distributions, skewness analysis, correlation matrices, and group breakdowns."
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please upload a dataset first.")
        return

    theme = st.session_state.get("theme", "dark")

    tab1, tab2, tab3, tab4 = st.tabs(["🔢 Numeric Analytics", "🔤 Categorical Distributions", "🔗 Correlation Matrix", "📊 Group Aggregations"])

    with tab1:
        st.subheader("Descriptive Statistics for Numeric Variables")
        num_summary = EDAEngine.get_numeric_summary(df)
        if not num_summary.empty:
            st.dataframe(num_summary, use_container_width=True)
            
            st.markdown("#### Distribution & Box Plots")
            num_cols = list(num_summary.index)
            sel_col = st.selectbox("Select Numeric Column to Inspect", num_cols)
            
            c1, c2 = st.columns(2)
            with c1:
                fig_hist = Visualizer.plot_histogram(df, sel_col, theme=theme)
                st.plotly_chart(fig_hist, use_container_width=True)
            with c2:
                fig_box = Visualizer.plot_box(df, y_col=sel_col, theme=theme)
                st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No numeric columns available in this dataset.")

    with tab2:
        st.subheader("Categorical Feature Analysis")
        cat_summary = EDAEngine.get_categorical_summary(df)
        if cat_summary:
            cat_cols = [c["column"] for c in cat_summary]
            sel_cat = st.selectbox("Select Categorical Column", cat_cols)
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                fig_bar = Visualizer.plot_bar(df, sel_cat, theme=theme)
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_c2:
                fig_donut = Visualizer.plot_donut(df, sel_cat, theme=theme)
                st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No categorical features available in this dataset.")

    with tab3:
        st.subheader("Pairwise Numeric Correlation")
        corr_method = st.radio("Correlation Method", ["pearson", "spearman"], horizontal=True)
        corr_df = EDAEngine.calculate_correlations(df, method=corr_method)
        
        if corr_df is not None:
            fig_heat = Visualizer.plot_correlation_heatmap(corr_df, theme=theme)
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.markdown("#### Top Correlated Relationships (|r| >= 0.5)")
            top_pairs = EDAEngine.get_top_correlations(corr_df, threshold=0.5)
            if top_pairs:
                st.dataframe(pd.DataFrame(top_pairs), use_container_width=True)
            else:
                st.caption("No strong pairwise correlations (|r| >= 0.5) found.")
        else:
            st.info("At least 2 numeric columns are required to calculate a correlation matrix.")

    with tab4:
        st.subheader("Group Aggregations")
        cat_cols = list(df.select_dtypes(include=["object", "category", "bool"]).columns)
        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        
        if cat_cols and num_cols:
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                grp_by = st.selectbox("Group By (Category)", cat_cols)
            with g_col2:
                agg_val = st.selectbox("Aggregate (Numeric)", num_cols)
                
            agg_df = EDAEngine.group_aggregation(df, grp_by, agg_val)
            st.dataframe(agg_df, use_container_width=True)
            
            # Grouped Box Plot
            fig_grp = Visualizer.plot_box(df, y_col=agg_val, x_col=grp_by, theme=theme)
            st.plotly_chart(fig_grp, use_container_width=True)
        else:
            st.info("Need both categorical and numeric columns for group aggregations.")

