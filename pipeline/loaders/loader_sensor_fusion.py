"""
loader_sensor_fusion.py
=======================
Loads Dataset 1: Bridge SHM multi-sensor CSV.
Returns a raw DataFrame with datetime index, sorted chronologically.
"""
import pandas as pd
from pathlib import Path

from pipeline.utils import get_logger, df_report
from pipeline.config import PATHS, LOGS_DIR


def load_sensor_fusion(path: Path = None) -> pd.DataFrame:
    log = get_logger("loader.sensor_fusion", LOGS_DIR)
    path = Path(path or PATHS["sensor_fusion"])
    log.info(f"Loading sensor fusion dataset from: {path}")

    df = pd.read_csv(path, low_memory=False)
    log.info(f"Raw shape: {df.shape}")

    # ── Parse timestamp ────────────────────────────────────────────────────────
    timestamp_col = None
    for col in df.columns:
        if "timestamp" in col.lower() or "time" in col.lower():
            timestamp_col = col
            break

    if timestamp_col:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
        df = df.sort_values(timestamp_col).reset_index(drop=True)
        df = df.rename(columns={timestamp_col: "Timestamp"})
        df = df.set_index("Timestamp")
        log.info(f"Timestamp range: {df.index.min()} → {df.index.max()}")
    else:
        log.warning("No timestamp column found — skipping datetime index")

    # ── Cast numeric columns to float32 ───────────────────────────────────────
    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype("float32")

    df_report(df, "sensor_fusion [raw]", log)
    return df
