"""
config.py
=========
Central configuration for all dataset paths, scaler choices, and pipeline parameters.
All paths are relative to the project ROOT (structure_intelligence/).
"""
import os
from pathlib import Path

# ─── ROOT PATHS ───────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent  # structure_intelligence/
DATASETS_DIR = ROOT_DIR / "datasets"
PROCESSED_DIR = ROOT_DIR / "processed"
SCALERS_DIR = ROOT_DIR / "processed" / "scalers"
LOGS_DIR = ROOT_DIR / "logs"

# ─── DATASET FILE PATHS ───────────────────────────────────────────────────────
PATHS = {
    "sensor_fusion": DATASETS_DIR / "1 [sensor fusion]"
        / "37544-extended_bridge_shm_dataset_timestamps_fixed - Sheet1.csv",

    "behaviour": DATASETS_DIR / "2 [behaviour analysis]"
        / "Bridge vibration monitoring dataset",  # directory containing test1..test8.txt

    "anomaly": DATASETS_DIR / "3 [anomaly detection]" / "bridge_monitoring_data.csv",

    "failure": DATASETS_DIR / "4 [failure prediction]" / "bridge_dataset.csv",

    "digital_twin": DATASETS_DIR / "5 [digital twin]" / "bridge_digital_twin_dataset.csv",
}

# ─── OUTPUT PARQUET FILES ─────────────────────────────────────────────────────
OUTPUT_FILES = {
    "sensor_fusion":   PROCESSED_DIR / "sensor_fusion.parquet",
    "behaviour":       PROCESSED_DIR / "behaviour.parquet",
    "anomaly":         PROCESSED_DIR / "anomaly.parquet",
    "failure":         PROCESSED_DIR / "failure_prediction.parquet",
    "digital_twin":    PROCESSED_DIR / "digital_twin.parquet",
}

# ─── SCALER SETTINGS ─────────────────────────────────────────────────────────
# "standard" → StandardScaler (mean=0, std=1)  — for raw physical measurements
# "minmax"   → MinMaxScaler  (0–1)             — for index/score/ratio columns
SCALER_CONFIG = {
    "sensor_fusion": "standard",
    "behaviour":     "standard",
    "anomaly":       "standard",
    "failure":       "standard",
    "digital_twin":  "standard",
}

# Columns that should use MinMaxScaler instead (overrides above per-column)
MINMAX_COLUMNS = {
    "failure":     ["Degradation_Score", "Forecast_Score"],
    "digital_twin": [
        "Structural_Health_Index_SHI",
        "Anomaly_Detection_Score",
        "Probability_of_Failure_PoF",
        "SHI_Predicted_24h_Ahead",
        "SHI_Predicted_7d_Ahead",
        "SHI_Predicted_30d_Ahead",
        "Corrosion_Level_percent",
        "Fatigue_Accumulation_au",
    ],
}

# ─── CLEANER SETTINGS ─────────────────────────────────────────────────────────
OUTLIER_IQR_FACTOR = 1.5   # IQR multiplier for clipping
MAX_NAN_PCT = 0.50         # drop column if > 50% NaN

# ─── FEATURE ENGINEERING ──────────────────────────────────────────────────────
# Behaviour (vibration TXT): sliding window params
VIBRATION_WINDOW_SAMPLES = 200    # 1 second at 200 Hz
VIBRATION_OVERLAP = 0.5           # 50% overlap

# Anomaly (216-sensor PCA)
PCA_COMPONENTS = 30               # target PCA dimensions

# Rolling window sizes (in rows/minutes) for DS1 and DS5
ROLLING_WINDOWS = [10, 30, 60]    # minutes

# Lag steps for DS4 and DS5 (in rows/minutes)
LAG_STEPS = [1, 6, 12, 24]

# ─── COLUMN METADATA ─────────────────────────────────────────────────────────
# Columns to NOT normalize (labels, IDs, flags, timestamps)
EXCLUDE_FROM_SCALING = {
    "sensor_fusion": ["Timestamp", "Damage_Label", "Maintenance_Flag",
                      "Sensor_Status", "GPS_Lat", "GPS_Long"],
    "behaviour":     ["time_s", "test_id"],
    "anomaly":       [],
    "failure":       ["Timestamp", "Bridge_ID", "Sensor_ID",
                      "Structural_Condition", "Damage_Class"],
    "digital_twin":  ["Timestamp", "Bridge_Mood_Meter", "Vibration_Anomaly_Location",
                      "Maintenance_Alert", "Flood_Event_Flag", "High_Winds_Storms",
                      "Landslide_Ground_Movement", "Abnormal_Traffic_Load_Surges",
                      "Localized_Strain_Hotspot"],
}

# Categorical columns to one-hot encode
CATEGORICAL_COLUMNS = {
    "failure":     ["Structural_Condition"],
    "digital_twin": ["Bridge_Mood_Meter", "Vibration_Anomaly_Location"],
}

# ─── MISC ─────────────────────────────────────────────────────────────────────
RANDOM_SEED = 42
LOG_LEVEL = "INFO"
