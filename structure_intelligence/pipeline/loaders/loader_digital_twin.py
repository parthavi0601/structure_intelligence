"""
loader_digital_twin.py
======================
Loads Dataset 5: bridge_digital_twin_dataset.csv — 54-column richest dataset.
Parses timestamp, standardizes column names, casts dtypes.
"""
import pandas as pd
from pathlib import Path

from pipeline.utils import get_logger, df_report
from pipeline.config import PATHS, LOGS_DIR


# Binary flag / event columns → keep as int8
BINARY_COLS = [
    "Maintenance_Alert", "Flood_Event_Flag", "High_Winds_Storms",
    "Landslide_Ground_Movement", "Abnormal_Traffic_Load_Surges",
    "Localized_Strain_Hotspot",
]

# Categorical text columns → keep as object/category
CATEGORICAL_COLS = ["Bridge_Mood_Meter", "Vibration_Anomaly_Location"]


def load_digital_twin(path: Path = None) -> pd.DataFrame:
    log = get_logger("loader.digital_twin", LOGS_DIR)
    path = Path(path or PATHS["digital_twin"])
    log.info(f"Loading digital twin dataset from: {path}")

    df = pd.read_csv(path, low_memory=False)
    log.info(f"Raw shape: {df.shape}")

    # ── Parse timestamp ────────────────────────────────────────────────────────
    for col in df.columns:
        if "timestamp" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.rename(columns={col: "Timestamp"})
            df = df.sort_values("Timestamp").reset_index(drop=True)
            df = df.set_index("Timestamp")
            log.info(f"Timestamp range: {df.index.min()} → {df.index.max()}")
            break

    # ── Strip column name whitespace ──────────────────────────────────────────
    df.columns = [c.strip() for c in df.columns]

    # ── Cast binary flag columns to int8 ──────────────────────────────────────
    for col in BINARY_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int8")

    # ── Cast categorical columns to category dtype ────────────────────────────
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # ── Cast remaining float64 → float32 ─────────────────────────────────────
    skip = set(BINARY_COLS + CATEGORICAL_COLS)
    for col in df.select_dtypes(include=["float64"]).columns:
        if col not in skip:
            df[col] = df[col].astype("float32")

    df_report(df, "digital_twin [raw]", log)
    return df
