"""
Configuration and settings for DataNova - Universal Smart Data Analytics Platform.
"""
from dataclasses import dataclass
from typing import Dict, Any

APP_NAME = "DataNova"
APP_TITLE = "DataNova — Universal Smart Data Analytics Platform"
APP_SUBTITLE = "Automated Data Profiling, Intelligent Cleaning, Exploratory Data Analysis, Interactive Visualization and Predictive Analytics"
VERSION = "1.0.0"

# Visualization themes
THEMES = {
    "dark": {
        "bg_color": "#0e1117",
        "card_bg": "#1e222d",
        "text_color": "#ffffff",
        "accent": "#2563eb",
        "secondary": "#0d9488",
        "plotly_template": "plotly_dark",
    },
    "light": {
        "bg_color": "#f8fafc",
        "card_bg": "#ffffff",
        "text_color": "#0f172a",
        "accent": "#2563eb",
        "secondary": "#0d9488",
        "plotly_template": "plotly_white",
    }
}

DEFAULT_SAMPLE_SIZE = 10000
MAX_CATEGORICAL_UNIQUE = 30
OUTLIER_IQR_FACTOR = 1.5

# Quality Score Weights: Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)
WEIGHT_MISSING = 0.50
WEIGHT_DUPLICATES = 0.25
WEIGHT_CONSTANT = 0.15
WEIGHT_INVALID = 0.10

@dataclass
class AppConfig:
    sample_limit: int = DEFAULT_SAMPLE_SIZE
    theme: str = "dark"
    enable_ml: bool = True
    enable_sampling_warning: bool = True

