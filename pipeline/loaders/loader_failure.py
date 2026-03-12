"""
loader_failure.py
=================
Loads Dataset 4: bridge_dataset.csv — multi-bridge failure prediction dataset.
Parses timestamp, casts types, returns sorted DataFrame.
"""
import pandas as pd
from pathlib import Path

from pipeline.utils import get_logger, df_report
from pipeline.config import PATHS, LOGS_DIR


def load_failure(path: Path = None) -> pd.DataFrame:
    log = get_logger("loader.failure", LOGS_DIR)
    path = Path(path or PATHS["failure"])
    log.info(f"Loading failure prediction dataset from: {path}")

    df = pd.read_csv(path, low_memory=False)
    log.info(f"Raw shape: {df.shape}")

    # ── Parse timestamp ────────────────────────────────────────────────────────
    for col in df.columns:
        if "timestamp" in col.lower() or col.lower() == "time":
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.rename(columns={col: "Timestamp"})
            df = df.sort_values("Timestamp").reset_index(drop=True)
            df = df.set_index("Timestamp")
            log.info(f"Timestamp range: {df.index.min()} → {df.index.max()}")
            break

    # ── Standardize column names (strip spaces) ───────────────────────────────
    df.columns = [c.strip() for c in df.columns]

    # ── Cast IDs as strings ───────────────────────────────────────────────────
    for id_col in ["Bridge_ID", "Sensor_ID"]:
        if id_col in df.columns:
            df[id_col] = df[id_col].astype(str)

    # ── Cast numeric columns to float32 ───────────────────────────────────────
    skip_cols = {"Bridge_ID", "Sensor_ID", "Structural_Condition", "Damage_Class"}
    for col in df.select_dtypes(include=["float64"]).columns:
        if col not in skip_cols:
            df[col] = df[col].astype("float32")

    df_report(df, "failure [raw]", log)
    return df
