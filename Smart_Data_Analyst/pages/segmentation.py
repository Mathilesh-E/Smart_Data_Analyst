"""
Page: Segmentation & Anomaly Detection
Unsupervised machine learning: K-Means clustering with 2D PCA projection,
silhouette scores, and Isolation Forest multivariate anomaly detection.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from smart_analyst.utils import render_hero
from smart_analyst.clustering import ClusteringEngine
from smart_analyst.anomaly_detection import AnomalyDetector
from smart_analyst.visualization import SDA_PALETTE

def render_segmentation_page():
    render_hero(
        title="Segmentation & Anomaly Detection",
        subtitle="Unsupervised machine learning: K-Means clustering, PCA projection, and Isolation Forest anomaly flagging.",
        badge="Unsupervised ML"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    num_cols = list(df.select_dtypes(include=[np.number]).columns)
    if len(num_cols) < 2:
        st.warning("Clustering and anomaly detection require at least 2 numeric features.")
        return

    tab1, tab2 = st.tabs(["🎯 K-Means Customer/Record Segmentation", "🔍 Isolation Forest Anomaly Detection"])

    with tab1:
        st.markdown("### K-Means Clustering")
        c1, c2 = st.columns([2, 1])
        with c1:
            sel_feats = st.multiselect("Clustering Features", num_cols, default=num_cols[:min(4, len(num_cols))])
        with c2:
            k = st.slider("Number of Clusters (k)", 2, 8, 3)

        if st.button("Run K-Means Clustering", type="primary"):
            if len(sel_feats) < 2:
                st.error("Please select at least 2 numeric features for clustering.")
            else:
                with st.spinner("Standardizing and fitting K-Means..."):
                    res = ClusteringEngine.run_kmeans(df, sel_feats, n_clusters=k)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success(f"Successfully segmented dataset into {k} clusters! (Silhouette: {res['silhouette_score']})")

                        # PCA Scatter plot
                        fig = px.scatter(
                            res["pca_df"],
                            x="PCA1",
                            y="PCA2",
                            color="Cluster",
                            color_discrete_sequence=SDA_PALETTE,
                            title=f"2D PCA Projection of {k} Clusters (Explained Variance: {sum(res['explained_variance'])*100:.1f}%)"
                        )
                        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.4)", font=dict(color="#cbd5e1"))
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("#### Cluster Feature Mean Profiles")
                        st.dataframe(res["cluster_means"], use_container_width=True)

    with tab2:
        st.markdown("### Isolation Forest Anomaly Detection")
        a1, a2 = st.columns([2, 1])
        with a1:
            iso_feats = st.multiselect("Anomaly Detection Features", num_cols, default=num_cols[:min(5, len(num_cols))], key="iso_f")
        with a2:
            contam = st.slider("Expected Contamination Rate", 0.01, 0.15, 0.05, step=0.01)

        if st.button("Detect Anomalies", type="primary"):
            if len(iso_feats) < 2:
                st.error("Please select at least 2 features.")
            else:
                with st.spinner("Evaluating multi-dimensional anomaly scores..."):
                    a_res = AnomalyDetector.detect_anomalies(df, iso_feats, contamination=contam)
                    if "error" in a_res:
                        st.error(a_res["error"])
                    else:
                        st.success(f"Detected **{a_res['anomalies_detected']}** anomalous records ({a_res['contamination_rate']*100}% threshold).")
                        st.dataframe(a_res["anomalies_df"], use_container_width=True)

