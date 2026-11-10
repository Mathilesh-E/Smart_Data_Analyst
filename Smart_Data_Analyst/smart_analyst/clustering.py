"""
Module: Segmentation & Clustering
Unsupervised machine learning: K-Means clustering with StandardScaler,
automatic silhouette evaluation, cluster profiling, and PCA 2D projections.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

class ClusteringEngine:

    @staticmethod
    def run_kmeans(df: pd.DataFrame, features: List[str], n_clusters: int = 3) -> Dict[str, Any]:
        """Runs K-Means clustering and returns assignments, silhouette, and profiles."""
        clean_df = df[features].dropna()
        if len(clean_df) < n_clusters * 2:
            return {"error": f"Insufficient sample size ({len(clean_df)} valid rows) for {n_clusters} clusters."}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(clean_df)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # Silhouette score
        sil_score = round(float(silhouette_score(X_scaled, labels)), 3) if len(clean_df) > n_clusters else 0.0

        # Cluster profiles (means)
        profile_df = clean_df.copy()
        profile_df["Cluster"] = labels
        cluster_means = profile_df.groupby("Cluster").mean().round(2)
        cluster_counts = profile_df["Cluster"].value_counts().to_dict()

        # PCA 2D coordinates for visualization
        pca = PCA(n_components=2)
        pca_coords = pca.fit_transform(X_scaled)
        pca_df = pd.DataFrame(pca_coords, columns=["PCA1", "PCA2"])
        pca_df["Cluster"] = [f"Cluster {l}" for l in labels]

        return {
            "n_clusters": n_clusters,
            "silhouette_score": sil_score,
            "cluster_counts": cluster_counts,
            "cluster_means": cluster_means,
            "pca_df": pca_df,
            "explained_variance": [round(float(v), 3) for v in pca.explained_variance_ratio_]
        }

