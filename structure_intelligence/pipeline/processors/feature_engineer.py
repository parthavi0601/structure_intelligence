"""
feature_engineer.py
===================
Dataset-specific feature engineering applied AFTER cleaning and transformation.

DS1 (sensor_fusion):  Rolling statistics (mean, std, RMS) on accelerometer channels
DS2 (behaviour):      Sliding-window FFT features (RMS, peak, crest, FFT dominant freq)
DS3 (anomaly):        PCA reduction to 30 components + reconstruction error
DS4 (failure):        Lag features for Degradation_Score; rolling 24h mean
DS5 (digital_twin):   Lag + rolling features for SHI; cumulative traffic; load interaction
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from sklearn.decomposition import PCA
import joblib

from pipeline.utils import get_logger, df_report, save_scaler
from pipeline.config import (
    LOGS_DIR, SCALERS_DIR,
    ROLLING_WINDOWS, LAG_STEPS,
    PCA_COMPONENTS,
    VIBRATION_WINDOW_SAMPLES, VIBRATION_OVERLAP,
)


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def _rms(arr: np.ndarray) -> float:
    return float(np.sqrt(np.mean(arr ** 2)))


def _crest_factor(arr: np.ndarray) -> float:
    rms = _rms(arr)
    return float(np.max(np.abs(arr)) / rms) if rms > 0 else 0.0


def _dominant_freq(arr: np.ndarray, fs: float = 200.0) -> float:
    fft_vals = np.abs(np.fft.rfft(arr))
    freqs    = np.fft.rfftfreq(len(arr), d=1.0 / fs)
    return float(freqs[np.argmax(fft_vals)])


def _spectral_energy(arr: np.ndarray) -> float:
    return float(np.sum(np.abs(np.fft.rfft(arr)) ** 2))


# ─── DS1: SENSOR FUSION ───────────────────────────────────────────────────────
def _engineer_sensor_fusion(df: pd.DataFrame, log) -> pd.DataFrame:
    accel_cols = [c for c in df.columns if c.lower().startswith("accel") or "acc" in c.lower()]
    if not accel_cols:
        log.warning("  No accelerometer columns detected for rolling features")
        return df

    log.info(f"  Computing rolling stats for {len(accel_cols)} accel columns, windows={ROLLING_WINDOWS}")
    for win in ROLLING_WINDOWS:
        roll = df[accel_cols].rolling(win, min_periods=1)
        df[[f"{c}_rmean_{win}" for c in accel_cols]] = roll.mean().astype("float32")
        df[[f"{c}_rstd_{win}"  for c in accel_cols]] = roll.std().fillna(0).astype("float32")
        # RMS over rolling window
        rms_df = df[accel_cols].pow(2).rolling(win, min_periods=1).mean().pow(0.5)
        df[[f"{c}_rrms_{win}"  for c in accel_cols]] = rms_df.astype("float32")

    log.info(f"  Added {len(accel_cols) * len(ROLLING_WINDOWS) * 3} rolling feature columns")
    return df


# ─── DS2: BEHAVIOUR (VIBRATION) ───────────────────────────────────────────────
def _engineer_behaviour(df: pd.DataFrame, log) -> pd.DataFrame:
    ch_cols  = [c for c in df.columns if c.startswith("ch") and c.endswith("_g")]
    step     = int(VIBRATION_WINDOW_SAMPLES * (1 - VIBRATION_OVERLAP))
    records  = []

    unique_tests = df["test_id"].unique() if "test_id" in df.columns else ["all"]

    for test_id in unique_tests:
        sub = df[df["test_id"] == test_id] if "test_id" in df.columns else df
        sub = sub.reset_index(drop=True)
        n   = len(sub)

        for start in range(0, n - VIBRATION_WINDOW_SAMPLES + 1, step):
            window = sub.iloc[start : start + VIBRATION_WINDOW_SAMPLES]
            row = {
                "test_id":     test_id,
                "window_start": start,
                "time_start_s": window["time_s"].iloc[0] if "time_s" in window.columns else np.nan,
            }
            for ch in ch_cols:
                arr = window[ch].values.astype(float)
                row[f"{ch}_rms"]          = _rms(arr)
                row[f"{ch}_peak"]         = float(np.max(np.abs(arr)))
                row[f"{ch}_crest"]        = _crest_factor(arr)
                row[f"{ch}_dom_freq_hz"]  = _dominant_freq(arr)
                row[f"{ch}_spec_energy"]  = _spectral_energy(arr)
                row[f"{ch}_kurtosis"]     = float(
                    pd.Series(arr).kurtosis() if len(arr) > 3 else 0.0
                )
            records.append(row)

    feat_df = pd.DataFrame(records)
    log.info(f"  Behaviour: {len(records)} windows, {feat_df.shape[1]} feature columns")
    return feat_df


# ─── DS3: ANOMALY (PCA) ───────────────────────────────────────────────────────
def _engineer_anomaly(df: pd.DataFrame, log, fit: bool, scaler_dir: Path) -> pd.DataFrame:
    sensor_cols = [c for c in df.columns if c.startswith("Sensor_")]
    if not sensor_cols:
        log.warning("  No Sensor_* columns found for PCA")
        return df

    X = df[sensor_cols].values

    if fit:
        pca = PCA(n_components=min(PCA_COMPONENTS, len(sensor_cols)), random_state=42)
        pca_vals = pca.fit_transform(X)
        save_scaler(pca, "anomaly_pca", scaler_dir, log)
        explained = pca.explained_variance_ratio_.cumsum()[-1]
        log.info(f"  PCA: {PCA_COMPONENTS} components explain {explained:.1%} variance")
    else:
        pca = joblib.load(scaler_dir / "anomaly_pca_scaler.pkl")
        pca_vals = pca.transform(X)

    pca_cols = [f"pca_{i+1:02d}" for i in range(pca_vals.shape[1])]
    pca_df   = pd.DataFrame(pca_vals, columns=pca_cols, index=df.index, dtype="float32")

    # Reconstruction error as unsupervised anomaly score
    X_recon  = pca.inverse_transform(pca_vals)
    recon_err = np.mean((X - X_recon) ** 2, axis=1).astype("float32")
    pca_df["reconstruction_error"] = recon_err

    result = pd.concat([df, pca_df], axis=1)
    log.info(f"  Added {len(pca_cols) + 1} PCA/reconstruction columns")
    return result


# ─── DS4: FAILURE PREDICTION ──────────────────────────────────────────────────
def _engineer_failure(df: pd.DataFrame, log) -> pd.DataFrame:
    target_cols = []
    for candidate in ["Degradation_Score", "Forecast_Score", "FFT_Peak_Frequency", "FFT_Magnitude"]:
        if candidate in df.columns:
            target_cols.append(candidate)

    if not target_cols:
        log.warning("  No target columns found for lag/rolling features in failure dataset")
        return df

    # Lag features
    for col in target_cols:
        for lag in LAG_STEPS:
            df[f"{col}_lag{lag}"] = df[col].shift(lag).astype("float32")

    # Rolling 24-step mean and std
    for col in target_cols:
        df[f"{col}_roll24_mean"] = df[col].rolling(24, min_periods=1).mean().astype("float32")
        df[f"{col}_roll24_std"]  = df[col].rolling(24, min_periods=1).std().fillna(0).astype("float32")

    # Cross-feature: Wind × Accel_Z (impact proxy)
    if "Wind_Speed_ms" in df.columns and "Acceleration_Z" in df.columns:
        df["wind_x_accelZ"] = (df["Wind_Speed_ms"] * df["Acceleration_Z"]).astype("float32")

    # RMS of X, Y, Z accelerations
    accel_xyz = [c for c in ["Acceleration_X", "Acceleration_Y", "Acceleration_Z"] if c in df.columns]
    if len(accel_xyz) == 3:
        df["accel_rms_xyz"] = np.sqrt(
            (df[accel_xyz] ** 2).mean(axis=1)
        ).astype("float32")

    # Fill NaNs introduced by lag/rolling (first rows)
    lag_cols = [c for c in df.columns if "_lag" in c or "_roll" in c]
    df[lag_cols] = df[lag_cols].bfill().ffill()

    log.info(f"  Failure: added {len(lag_cols)} lag/rolling + cross feature columns")
    return df


# ─── DS5: DIGITAL TWIN ────────────────────────────────────────────────────────
def _engineer_digital_twin(df: pd.DataFrame, log) -> pd.DataFrame:
    shi_col = "Structural_Health_Index_SHI" if "Structural_Health_Index_SHI" in df.columns else None

    # Lag features on SHI
    if shi_col:
        for lag in LAG_STEPS:
            df[f"SHI_lag{lag}"] = df[shi_col].shift(lag).astype("float32")
        log.info(f"  Added SHI lag features: {LAG_STEPS}")

    # Rolling stats on SHI + Vibration + Strain
    core_cols = [c for c in ["Structural_Health_Index_SHI", "Vibration_ms2", "Strain_microstrain"]
                 if c in df.columns]
    for col in core_cols:
        for win in ROLLING_WINDOWS:
            df[f"{col}_rmean_{win}"] = df[col].rolling(win, min_periods=1).mean().astype("float32")
            df[f"{col}_rstd_{win}"]  = df[col].rolling(win, min_periods=1).std().fillna(0).astype("float32")

    # Cumulative traffic index
    if "Traffic_Volume_vph" in df.columns:
        df["cum_traffic"] = df["Traffic_Volume_vph"].cumsum().astype("float32")

    # Load interaction: Vehicle_Load × Axle_Counts
    if "Vehicle_Load_tons" in df.columns and "Axle_Counts_pmin" in df.columns:
        df["load_x_axle"] = (df["Vehicle_Load_tons"] * df["Axle_Counts_pmin"]).astype("float32")

    # SHI rate of change
    if shi_col:
        df["SHI_delta"] = df[shi_col].diff().fillna(0).astype("float32")

    # Fill lag-introduced NaNs
    lag_cols = [c for c in df.columns if "_lag" in c or "_rmean" in c or "_rstd" in c]
    df[lag_cols] = df[lag_cols].bfill().ffill()

    log.info(f"  Digital twin: added {len(lag_cols)} lag/rolling + {3} derived feature columns")
    return df


# ─── MAIN ENTRY POINT ─────────────────────────────────────────────────────────
def engineer_features(
    df: pd.DataFrame,
    dataset_name: str,
    fit: bool = True,
    scaler_dir: Optional[Path] = None,
) -> pd.DataFrame:
    log = get_logger("processor.feature_engineer", LOGS_DIR)
    log.info(f"[{dataset_name}] Feature engineering. Input shape: {df.shape}")
    scaler_dir = Path(scaler_dir or SCALERS_DIR)

    if dataset_name == "sensor_fusion":
        df = _engineer_sensor_fusion(df, log)
    elif dataset_name == "behaviour":
        df = _engineer_behaviour(df, log)
    elif dataset_name == "anomaly":
        df = _engineer_anomaly(df, log, fit=fit, scaler_dir=scaler_dir)
    elif dataset_name == "failure":
        df = _engineer_failure(df, log)
    elif dataset_name == "digital_twin":
        df = _engineer_digital_twin(df, log)
    else:
        log.warning(f"  Unknown dataset_name: {dataset_name} — skipping feature engineering")

    df_report(df, f"{dataset_name} [engineered]", log)
    return df
