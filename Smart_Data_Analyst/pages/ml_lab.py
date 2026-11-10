"""
Page: Machine Learning Lab
Optional, leakage-free predictive analytics: auto-infers Classification vs Regression,
benchmarks multiple models, produces evaluation leaderboards & feature importances.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from smart_analyst.utils import render_hero
from smart_analyst.machine_learning import MachineLearningLab
from smart_analyst.visualization import SDA_PALETTE

def render_ml_lab_page():
    render_hero(
        title="Predictive Machine Learning Lab",
        subtitle="Zero-leakage automated pipelines, baseline model benchmarking, evaluation leaderboards, and feature importance.",
        badge="Predictive ML"
    )

    df = st.session_state.get("df_active")
    if df is None:
        st.info("Please load or upload a dataset first.")
        return

    all_cols = list(df.columns)
    c1, c2 = st.columns(2)
    with c1:
        target_col = st.selectbox("Target Variable (Y)", all_cols)

    inferred_task = MachineLearningLab.infer_task(df[target_col])
    with c2:
        task_type = st.radio("Inferred Task", ["Classification", "Regression"], index=0 if inferred_task == "Classification" else 1, horizontal=True)

    avail_feats = [c for c in all_cols if c != target_col]
    sel_feats = st.multiselect("Predictor Features (X)", avail_feats, default=avail_feats[:min(8, len(avail_feats))])

    if st.button("🚀 Train & Benchmark Models", type="primary"):
        with st.spinner("Training baseline models..."):
            res, err = MachineLearningLab.build_and_evaluate(df, target_col, sel_feats, task_type)
            if err:
                st.error(err)
            else:
                st.session_state["ml_results"] = res
                st.success("Model benchmarking completed successfully!")

    ml_res = st.session_state.get("ml_results")
    if ml_res:
        st.markdown("---")
        st.subheader("Model Performance Leaderboard")

        bench = ml_res.get("benchmark", {})
        rows = []
        for name, data in bench.items():
            if "error" not in data:
                r = {"Model": name}
                for k, v in data.items():
                    if k not in ["Confusion_Matrix", "Feature_Importance"]:
                        r[k] = v
                rows.append(r)

        if rows:
            st.table(pd.DataFrame(rows))

        # Model inspection
        st.markdown("### Model Diagnostics")
        chosen_m = st.selectbox("Inspect Model Details", list(bench.keys()))
        m_data = bench.get(chosen_m, {})

        if "Feature_Importance" in m_data:
            fi = m_data["Feature_Importance"]
            st.markdown(f"**Top Feature Importances ({chosen_m})**")
            fi_df = pd.DataFrame(list(fi.items()), columns=["Feature", "Importance"]).sort_values(by="Importance", ascending=True)
            fig = px.bar(fi_df, y="Feature", x="Importance", orientation="h", color_discrete_sequence=[SDA_PALETTE[0]])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.4)", font=dict(color="#cbd5e1"))
            st.plotly_chart(fig, use_container_width=True)

        if "Confusion_Matrix" in m_data:
            st.markdown(f"**Confusion Matrix ({chosen_m})**")
            cm = m_data["Confusion_Matrix"]
            fig_cm = px.imshow(cm, text_auto=True, color_continuous_scale="Blues")
            fig_cm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15, 23, 42, 0.4)", font=dict(color="#cbd5e1"))
            st.plotly_chart(fig_cm, use_container_width=True)
