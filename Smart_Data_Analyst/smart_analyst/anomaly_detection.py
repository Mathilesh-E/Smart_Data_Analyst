"""
Module: Anomaly Detection
Unsupervised multivariate outlier and anomaly detection using Isolation Forest.
Provides anomaly scoring, threshold contamination, and candidate review list.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetector:

    @staticmethod
    def detect_anomalies(df: pd.DataFrame, features: List[str], contamination: float = 0.05) -> Dict[str, Any]:
        """Runs Isolation Forest on numeric features to detect multidimensional anomalies."""
        sub_df = df[features].dropna()
        if len(sub_df) < 15:
            return {"error": "Insufficient valid records (minimum 15 required for anomaly detection)."}

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(sub_df)

        iso = IsolationForest(contamination=contamination, random_state=42)
        preds = iso.fit_predict(X_scaled) # -1 is anomaly, 1 is normal
        scores = iso.decision_function(X_scaled)

        result_df = sub_df.copy()
        result_df["Anomaly_Score"] = np.round(scores, 3)
        result_df["Is_Anomaly"] = preds == -1

        anomalies_only = result_df[result_df["Is_Anomaly"]]

        return {
            "total_analyzed": len(sub_df),
            "anomalies_detected": int((preds == -1).sum()),
            "contamination_rate": contamination,
            "anomalies_df": anomalies_only.sort_values(by="Anomaly_Score")
        }

