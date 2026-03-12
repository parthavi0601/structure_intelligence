"""
cleaner.py
==========
Dataset-agnostic cleaning:
  1. Drop fully-duplicate rows
  2. Drop columns with > MAX_NAN_PCT missing values
  3. Impute remaining NaNs (numeric: interpolate→ffill→bfill; categorical: mode)
  4. Clip outliers using IQR method on numeric columns (skips label/flag cols)
  5. Sort by index if datetime
"""
import numpy as np
import pandas as pd
from typing import List, Optional

from pipeline.utils import get_logger, df_report
from pipeline.config import OUTLIER_IQR_FACTOR, MAX_NAN_PCT, LOGS_DIR, EXCLUDE_FROM_SCALING


def clean(
    df: pd.DataFrame,
    dataset_name: str,
    skip_outlier_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    log = get_logger("processor.cleaner", LOGS_DIR)
    log.info(f"[{dataset_name}] Starting cleaning. Input shape: {df.shape}")

    df = df.copy()

    # ── 1. Drop duplicate rows ────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    log.info(f"  Dedup: removed {before - len(df)} rows")

    # ── 2. Drop columns with too many NaNs ────────────────────────────────────
    nan_pct = df.isna().mean()
    drop_cols = nan_pct[nan_pct > MAX_NAN_PCT].index.tolist()
    if drop_cols:
        log.info(f"  Dropping {len(drop_cols)} columns with >{MAX_NAN_PCT*100:.0f}% NaN: {drop_cols}")
        df = df.drop(columns=drop_cols)

    # ── 3. Impute NaNs ────────────────────────────────────────────────────────
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Numeric: interpolate + fill edges
    if num_cols:
        df[num_cols] = (
            df[num_cols]
            .interpolate(method="linear", limit_direction="both")
            .ffill()
            .bfill()
        )

    # Categorical: fill with mode
    for col in cat_cols:
        if df[col].isna().any():
            mode_val = df[col].mode(dropna=True)
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val.iloc[0])

    nan_remaining = df.isna().sum().sum()
    log.info(f"  After imputation: {nan_remaining} NaN values remain")

    # ── 4. Outlier clipping (IQR) ─────────────────────────────────────────────
    # Build the list of columns to skip during clipping
    exclude = set(EXCLUDE_FROM_SCALING.get(dataset_name, []))
    if skip_outlier_cols:
        exclude.update(skip_outlier_cols)

    clip_cols = [c for c in num_cols if c not in exclude]
    clipped_count = 0
    for col in clip_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo = q1 - OUTLIER_IQR_FACTOR * iqr
        hi = q3 + OUTLIER_IQR_FACTOR * iqr
        n_clipped = ((df[col] < lo) | (df[col] > hi)).sum()
        df[col] = df[col].clip(lower=lo, upper=hi)
        clipped_count += n_clipped

    log.info(f"  Outlier clipping: {clipped_count} values clipped across {len(clip_cols)} columns")

    # ── 5. Sort by datetime index if applicable ────────────────────────────────
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.sort_index()

    df_report(df, f"{dataset_name} [cleaned]", log)
    return df
