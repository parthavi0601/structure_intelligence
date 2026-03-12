"""
loader_anomaly.py
=================
Loads Dataset 3: bridge_monitoring_data.csv — 216 unnamed sensor columns.
Renames columns to Sensor_001 … Sensor_216, casts to float32.
"""
import pandas as pd
from pathlib import Path

from pipeline.utils import get_logger, df_report
from pipeline.config import PATHS, LOGS_DIR


def load_anomaly(path: Path = None) -> pd.DataFrame:
    log = get_logger("loader.anomaly", LOGS_DIR)
    path = Path(path or PATHS["anomaly"])
    log.info(f"Loading anomaly detection dataset from: {path}")

    df = pd.read_csv(path, low_memory=False)
    log.info(f"Raw shape: {df.shape}")

    # ── Detect and rename sensor columns ──────────────────────────────────────
    # Keep any non-numeric metadata columns as-is; rename numeric sensor cols
    timestamp_col = None
    new_names = {}
    sensor_idx = 1
    for col in df.columns:
        lc = col.lower().strip()
        if "time" in lc or "timestamp" in lc or "date" in lc:
            timestamp_col = col
            new_names[col] = "Timestamp"
        elif "id" in lc or "label" in lc or "class" in lc:
            pass  # keep original name
        else:
            new_names[col] = f"Sensor_{sensor_idx:03d}"
            sensor_idx += 1

    df = df.rename(columns=new_names)
    log.info(f"Renamed {sensor_idx - 1} sensor columns (Sensor_001 … Sensor_{sensor_idx-1:03d})")

    # ── Parse timestamp if found ───────────────────────────────────────────────
    if timestamp_col and "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.sort_values("Timestamp").reset_index(drop=True)
        df = df.set_index("Timestamp")
        log.info(f"Timestamp range: {df.index.min()} → {df.index.max()}")
    else:
        # No timestamp — add a synthetic integer index column
        df.index.name = "sample_idx"
        log.info("No timestamp column found — using integer sample index")

    # ── Cast to float32 ───────────────────────────────────────────────────────
    sensor_cols = [c for c in df.columns if c.startswith("Sensor_")]
    df[sensor_cols] = df[sensor_cols].astype("float32")

    df_report(df, "anomaly [raw]", log)
    return df
