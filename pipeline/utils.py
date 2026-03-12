"""
utils.py
========
Shared helpers: logging setup, save/load utilities, timing decorator.
"""
import logging
import sys
import io
import time
import json
from pathlib import Path
from functools import wraps

import pandas as pd
import joblib


# ─── LOGGING ──────────────────────────────────────────────────────────────────
def get_logger(name: str, log_dir: Path = None, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # console handler — force UTF-8 so emoji chars don't crash on Windows cp1252
    try:
        stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except AttributeError:
        stream = sys.stdout  # fallback (e.g. in pytest)
    ch = logging.StreamHandler(stream)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # file handler (optional)
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / f"{name}.log")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# ─── TIMING DECORATOR ─────────────────────────────────────────────────────────
def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        log = get_logger(func.__module__)
        log.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


# ─── SAVE / LOAD ──────────────────────────────────────────────────────────────
def save_parquet(df: pd.DataFrame, path: Path, logger: logging.Logger = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=True, engine="pyarrow")
    if logger:
        logger.info(f"Saved {df.shape} → {path}")


def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path), engine="pyarrow")


def save_scaler(scaler, name: str, scaler_dir: Path, logger: logging.Logger = None):
    scaler_dir = Path(scaler_dir)
    scaler_dir.mkdir(parents=True, exist_ok=True)
    out = scaler_dir / f"{name}_scaler.pkl"
    joblib.dump(scaler, out)
    if logger:
        logger.info(f"Saved scaler → {out}")


def load_scaler(name: str, scaler_dir: Path):
    return joblib.load(Path(scaler_dir) / f"{name}_scaler.pkl")


# ─── STATS REPORT ─────────────────────────────────────────────────────────────
def df_report(df: pd.DataFrame, label: str, logger: logging.Logger) -> None:
    """Log a concise shape / NaN / dtype summary."""
    nan_count = df.isna().sum().sum()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    logger.info(
        f"[{label}] shape={df.shape} | NaN={nan_count} "
        f"| numeric_cols={len(numeric_cols)} | dtypes: {dict(df.dtypes.value_counts())}"
    )


def save_report(report: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)
