"""
transformer.py
==============
Normalization, encoding, and temporal feature extraction:
  1. StandardScaler on physical measurement columns
  2. MinMaxScaler on score/index columns (per MINMAX_COLUMNS config)
  3. Binary flag columns → int (0/1)
  4. One-hot encode categorical columns
  5. Cyclic sin/cos encoding of hour, day-of-week, month from DatetimeIndex
  6. Saves fitted scalers as .pkl for inference re-use
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
import joblib

from pipeline.utils import get_logger, df_report, save_scaler
from pipeline.config import (
    LOGS_DIR, SCALERS_DIR, EXCLUDE_FROM_SCALING,
    MINMAX_COLUMNS, CATEGORICAL_COLUMNS,
)


def _cyclic_encode(series: pd.Series, max_val: float) -> tuple:
    """Return (sin_series, cos_series) for cyclic encoding."""
    rad = 2 * np.pi * series / max_val
    return np.sin(rad), np.cos(rad)


def transform(
    df: pd.DataFrame,
    dataset_name: str,
    fit: bool = True,           # True = fit+transform (training), False = transform only
    scaler_dir: Optional[Path] = None,
) -> pd.DataFrame:
    log = get_logger("processor.transformer", LOGS_DIR)
    log.info(f"[{dataset_name}] Starting transformation. Input shape: {df.shape}")
    scaler_dir = Path(scaler_dir or SCALERS_DIR)
    df = df.copy()

    # ── 1. Cyclic temporal features from DatetimeIndex ────────────────────────
    if isinstance(df.index, pd.DatetimeIndex):
        df["hour_sin"], df["hour_cos"]         = _cyclic_encode(df.index.hour, 24)
        df["dow_sin"],  df["dow_cos"]           = _cyclic_encode(df.index.dayofweek, 7)
        df["month_sin"], df["month_cos"]        = _cyclic_encode(df.index.month, 12)
        log.info("  Added cyclic hour/dow/month features")

    # ── 2. Encode categorical columns ─────────────────────────────────────────
    cat_cols = CATEGORICAL_COLUMNS.get(dataset_name, [])
    for col in cat_cols:
        if col not in df.columns:
            continue
        dummies = pd.get_dummies(df[col], prefix=col, drop_first=False, dtype="int8")
        df = df.drop(columns=[col]).join(dummies)
        log.info(f"  One-hot encoded '{col}' → {list(dummies.columns)}")

    # ── 3. Encode label columns (Damage_Class) ────────────────────────────────
    if dataset_name == "failure" and "Damage_Class" in df.columns:
        le = LabelEncoder()
        df["Damage_Class_enc"] = le.fit_transform(df["Damage_Class"].astype(str))
        if fit:
            save_scaler(le, f"{dataset_name}_label", scaler_dir, log)
        log.info(f"  Label-encoded 'Damage_Class' → Damage_Class_enc")

    # ── 4. Identify numeric columns for scaling ────────────────────────────────
    exclude = set(EXCLUDE_FROM_SCALING.get(dataset_name, []))
    # also exclude newly-added binary/dummy cols from scaling
    exclude.update([c for c in df.columns if df[c].dtype == "int8"])
    exclude.update([c for c in df.columns if c.endswith("_enc")])

    all_num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    minmax_cols  = [c for c in MINMAX_COLUMNS.get(dataset_name, []) if c in df.columns]
    std_cols     = [c for c in all_num_cols
                    if c not in exclude and c not in minmax_cols
                    and not c.startswith("hour_") and not c.startswith("dow_")
                    and not c.startswith("month_")]

    # ── 5. StandardScaler ─────────────────────────────────────────────────────
    if std_cols:
        if fit:
            ss = StandardScaler()
            df[std_cols] = ss.fit_transform(df[std_cols]).astype("float32")
            save_scaler(ss, f"{dataset_name}_standard", scaler_dir, log)
        else:
            ss = joblib.load(scaler_dir / f"{dataset_name}_standard_scaler.pkl")
            df[std_cols] = ss.transform(df[std_cols]).astype("float32")
        log.info(f"  StandardScaler applied to {len(std_cols)} columns")

    # ── 6. MinMaxScaler ───────────────────────────────────────────────────────
    if minmax_cols:
        if fit:
            mm = MinMaxScaler()
            df[minmax_cols] = mm.fit_transform(df[minmax_cols]).astype("float32")
            save_scaler(mm, f"{dataset_name}_minmax", scaler_dir, log)
        else:
            mm = joblib.load(scaler_dir / f"{dataset_name}_minmax_scaler.pkl")
            df[minmax_cols] = mm.transform(df[minmax_cols]).astype("float32")
        log.info(f"  MinMaxScaler applied to {len(minmax_cols)} columns")

    df_report(df, f"{dataset_name} [transformed]", log)
    return df
