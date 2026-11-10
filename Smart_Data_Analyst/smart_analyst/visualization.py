"""
Module: Dynamic Visualization Studio
Generates responsive, beautiful Plotly charts with a cohesive dark palette,
glassmorphic styling, and intelligent sampling for instant rendering.
"""
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Enterprise Theme Palette
SDA_PALETTE = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#38bdf8", "#f43f5e"]
SAMPLE_ROW_LIMIT = 10000

class Visualizer:

    @staticmethod
    def sample_if_large(df: pd.DataFrame) -> (pd.DataFrame, bool):
        """Samples dataframe if row count exceeds fluid interactive threshold."""
        if len(df) > SAMPLE_ROW_LIMIT:
            return df.sample(n=SAMPLE_ROW_LIMIT, random_state=42), True
        return df, False

    @staticmethod
    def style_figure(fig: go.Figure, title: str = "") -> go.Figure:
        """Applies consistent executive dark styling to Plotly figures."""
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=15, color="#f8fafc", family="Plus Jakarta Sans, sans-serif")
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            font=dict(color="#94a3b8", family="Plus Jakarta Sans, sans-serif"),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="closest",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, color="#cbd5e1")
            )
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 255, 255, 0.06)", zeroline=False)
        return fig

    @staticmethod
    def plot_histogram(df: pd.DataFrame, col: str, bins: int = 30, color_by: str = None) -> go.Figure:
        sample_df, sampled = Visualizer.sample_if_large(df)
        fig = px.histogram(
            sample_df,
            x=col,
            color=color_by if color_by in sample_df.columns else None,
            nbins=bins,
            marginal="box",
            color_discrete_sequence=SDA_PALETTE
        )
        return Visualizer.style_figure(fig, f"Distribution of {col}" + (" (Sampled)" if sampled else ""))

    @staticmethod
    def plot_box(df: pd.DataFrame, y_col: str, x_col: str = None) -> go.Figure:
        sample_df, sampled = Visualizer.sample_if_large(df)
        fig = px.box(
            sample_df,
            y=y_col,
            x=x_col if x_col in sample_df.columns else None,
            points="outliers",
            color=x_col if x_col in sample_df.columns else None,
            color_discrete_sequence=SDA_PALETTE
        )
        return Visualizer.style_figure(fig, f"Box Plot: {y_col}" + (f" by {x_col}" if x_col else ""))

    @staticmethod
    def plot_bar(df: pd.DataFrame, col: str, top_n: int = 15, horizontal: bool = False) -> go.Figure:
        val_counts = df[col].value_counts().head(top_n).reset_index()
        val_counts.columns = [col, "Count"]
        if horizontal:
            fig = px.bar(val_counts, y=col, x="Count", orientation="h", color_discrete_sequence=[SDA_PALETTE[0]])
            fig.update_layout(yaxis=dict(autorange="reversed"))
        else:
            fig = px.bar(val_counts, x=col, y="Count", color_discrete_sequence=[SDA_PALETTE[0]])
        return Visualizer.style_figure(fig, f"Top {top_n} Frequencies in {col}")

    @staticmethod
    def plot_donut(df: pd.DataFrame, col: str, top_n: int = 8) -> go.Figure:
        val_counts = df[col].value_counts().head(top_n).reset_index()
        val_counts.columns = [col, "Count"]
        fig = px.pie(
            val_counts,
            names=col,
            values="Count",
            hole=0.5,
            color_discrete_sequence=SDA_PALETTE
        )
        return Visualizer.style_figure(fig, f"Proportions: {col}")

    @staticmethod
    def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str, color_by: str = None, size_by: str = None) -> go.Figure:
        sample_df, sampled = Visualizer.sample_if_large(df)
        fig = px.scatter(
            sample_df,
            x=x_col,
            y=y_col,
            color=color_by if color_by in sample_df.columns else None,
            size=size_by if size_by in sample_df.columns else None,
            color_discrete_sequence=SDA_PALETTE,
            opacity=0.8
        )
        return Visualizer.style_figure(fig, f"{y_col} vs {x_col}" + (" (Sampled)" if sampled else ""))

    @staticmethod
    def plot_line(df: pd.DataFrame, x_col: str, y_col: str, group_by: str = None) -> go.Figure:
        sort_df = df.sort_values(by=x_col)
        fig = px.line(
            sort_df,
            x=x_col,
            y=y_col,
            color=group_by if group_by in sort_df.columns else None,
            color_discrete_sequence=SDA_PALETTE
        )
        return Visualizer.style_figure(fig, f"Trend: {y_col} over {x_col}")

    @staticmethod
    def plot_heatmap(corr_df: pd.DataFrame) -> go.Figure:
        fig = px.imshow(
            corr_df,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="Viridis",
            zmin=-1,
            zmax=1
        )
        return Visualizer.style_figure(fig, "Feature Correlation Heatmap")

