"""
Page: Advanced Visualization Studio
Interactive Plotly chart studio: Histograms, Box plots, Scatter plots,
Line/trend charts, Bar charts, and Donut charts with customizable color groupings.
"""
import streamlit as st
import pandas as pd
import numpy as np
from smart_analyst.utils import render_hero
from smart_analyst.visualization import Visualizer

def render_visualization_page():
    render_hero(
        title="Advanced Visualization Studio",
        subtitle="Custom interactive Plotly chart laboratory with adaptive groupings and responsive styling.",
        badge="Plotly Studio"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    all_cols = list(df.columns)
    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    cat_cols = list(df.select_dtypes(include=["object", "category", "bool"]).columns)

    st.markdown("### 📊 Interactive Chart Configurator")
    col1, col2, col3 = st.columns(3)

    chart_types = [
        "Histogram / Distribution",
        "Box Plot",
        "Bar Chart",
        "Scatter Plot",
        "Line / Trend Chart",
        "Donut Proportions"
    ]

    with col1:
        chart_type = st.selectbox("Select Chart Family", chart_types)
    with col2:
        x_col = st.selectbox("Primary Attribute (X-Axis / Variable)", all_cols)
    with col3:
        color_col = st.selectbox("Color / Group Dimension (Optional)", ["None"] + cat_cols)
        color_arg = None if color_col == "None" else color_col

    try:
        if chart_type == "Histogram / Distribution":
            bins = st.slider("Number of Bins", 10, 80, 30)
            fig = Visualizer.plot_histogram(df, x_col, bins=bins, color_by=color_arg)

        elif chart_type == "Box Plot":
            fig = Visualizer.plot_box(df, y_col=x_col, x_col=color_arg)

        elif chart_type == "Bar Chart":
            top_n = st.slider("Top N Categories", 5, 30, 15)
            is_horiz = st.checkbox("Horizontal Orientation", value=False)
            fig = Visualizer.plot_bar(df, x_col, top_n=top_n, horizontal=is_horiz)

        elif chart_type == "Scatter Plot":
            if not num_cols or len(num_cols) < 2:
                st.warning("Scatter plot requires numeric columns.")
                return
            y_col = st.selectbox("Y-Axis (Numeric)", num_cols, index=min(1, len(num_cols)-1))
            fig = Visualizer.plot_scatter(df, x_col=x_col, y_col=y_col, color_by=color_arg)

        elif chart_type == "Line / Trend Chart":
            if not num_cols:
                st.warning("Line chart requires numeric Y-Axis metric.")
                return
            y_col = st.selectbox("Y-Axis Measure", num_cols)
            fig = Visualizer.plot_line(df, x_col=x_col, y_col=y_col, group_by=color_arg)

        elif chart_type == "Donut Proportions":
            top_n = st.slider("Max Categories", 3, 12, 8)
            fig = Visualizer.plot_donut(df, x_col, top_n=top_n)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Could not render chart: {str(e)}")

