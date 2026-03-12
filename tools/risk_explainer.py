"""
tools/risk_explainer.py
=======================
Tool 2: Risk Explanation Engine
Given a structural asset identifier, explains WHY it has a high risk score
by breaking down the individual contributing AI-generated indicators.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import (
    PROCESSED_DIR, PREFERRED_DATASETS,
    CRITICAL_RISK, HIGH_RISK, HIGH_ANOMALY, HIGH_SHIFT
)


def _find_asset_data(asset_hint: str) -> tuple[str, pd.DataFrame | None]:
    """
    Attempts to locate a specific asset's data across all parquet datasets.
    Searches for `bridge_id`, `sensor_id`, or `test_id` columns matching the hint.
    Falls back to the highest-risk dataset if no match found.
    """
    asset_hint_lower = asset_hint.lower().strip()

    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if not fpath.exists():
            continue
        try:
            df = pd.read_parquet(fpath)
            # Try to find by ID columns
            for id_col in ['bridge_id', 'Bridge_ID', 'sensor_id', 'Sensor_ID', 'test_id']:
                if id_col in df.columns:
                    mask = df[id_col].astype(str).str.lower().str.contains(asset_hint_lower, na=False)
                    if mask.any():
                        return (fname.replace(".parquet", ""), df[mask])
        except Exception:
            continue

    # Fallback: use failure_prediction dataset (most likely to have bridge info)
    fallback = PROCESSED_DIR / "failure_prediction_behavior.parquet"
    if not fallback.exists():
        # try first available
        for fname in PREFERRED_DATASETS:
            fpath = PROCESSED_DIR / fname
            if fpath.exists():
                return (fname.replace(".parquet", ""), pd.read_parquet(fpath))
        return ("none", None)

    return ("failure_prediction_behavior", pd.read_parquet(fallback))


def explain_high_risk(asset_query: str) -> str:
    """
    Tool 2: Risk Explanation Engine
    Explains why a structure has high risk by analyzing its AI-generated
    structural indicators.

    Args:
        asset_query: Asset name or ID to investigate (e.g., "Bridge A", "B001").

    Returns:
        A detailed engineering explanation of the risk factors.
    """
    dataset_name, df = _find_asset_data(asset_query)

    if df is None or len(df) == 0:
        return f"ERROR: Could not find data for asset '{asset_query}'. Check the asset identifier."

    lines = ["=" * 60]
    lines.append(f"  RISK EXPLANATION REPORT")
    lines.append(f"  Asset Query: {asset_query}")
    lines.append(f"  Source Dataset: {dataset_name}")
    lines.append("=" * 60)

    n = len(df)
    lines.append(f"\nData Points Analyzed: {n:,}")

    # ─── Risk Score Analysis ────────────────────────────────────────────────
    risk_col = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
    if risk_col:
        risk_mean = df[risk_col].mean()
        risk_max  = df[risk_col].max()
        risk_min  = df[risk_col].min()
        risk_label = "CRITICAL" if risk_max >= CRITICAL_RISK else ("HIGH" if risk_max >= HIGH_RISK else "MODERATE")
        lines.append(f"\n[FAILURE RISK SCORE]")
        lines.append(f"  Current Mean Risk    : {risk_mean:.4f}")
        lines.append(f"  Peak Risk Observed   : {risk_max:.4f}  → {risk_label}")
        lines.append(f"  Minimum Risk         : {risk_min:.4f}")

        # Trend analysis
        if n > 10:
            first_half_avg = df[risk_col].iloc[:n//2].mean()
            second_half_avg = df[risk_col].iloc[n//2:].mean()
            trend = second_half_avg - first_half_avg
            trend_label = "DETERIORATING ↑" if trend > 0.05 else ("IMPROVING ↓" if trend < -0.05 else "STABLE →")
            lines.append(f"  Risk Trend           : {trend_label}  (Δ {trend:+.4f})")

    # ─── Anomaly Score Analysis ─────────────────────────────────────────────
    anomaly_col = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
    alert_col   = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)
    if anomaly_col:
        a_mean     = df[anomaly_col].mean()
        a_max      = df[anomaly_col].max()
        a_spikes   = (df[anomaly_col] >= HIGH_ANOMALY).sum()
        alert_cnt  = int(df[alert_col].sum()) if alert_col else "N/A"
        a_flag     = "ABNORMAL SENSOR RESPONSE" if a_max >= HIGH_ANOMALY else "Within Expected Bounds"
        lines.append(f"\n[ANOMALY DETECTION]")
        lines.append(f"  Mean Anomaly Score   : {a_mean:.4f}")
        lines.append(f"  Peak Anomaly Spike   : {a_max:.4f}  → {a_flag}")
        lines.append(f"  High-Anomaly Events  : {int(a_spikes)} readings ≥ {HIGH_ANOMALY}")
        lines.append(f"  Formal Alert Flags   : {alert_cnt}")
        if a_max >= HIGH_ANOMALY:
            lines.append(f"  → Autoencoder could not reconstruct sensor signals accurately, indicating")
            lines.append(f"    patterns outside the learned 'healthy structural behavior' profile.")

    # ─── Behavioral Shift Analysis ──────────────────────────────────────────
    shift_col    = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
    dynamics_col = next((c for c in df.columns if 'Structural_Dynamics_Score' in c), None)
    cluster_col  = next((c for c in df.columns if 'Behavioral_State_Cluster' in c), None)
    if shift_col:
        s_mean = df[shift_col].mean()
        s_max  = df[shift_col].max()
        s_label = "SIGNIFICANT MODAL DRIFT" if s_max >= HIGH_SHIFT else "Moderate Drift"
        lines.append(f"\n[BEHAVIORAL ANALYSIS]")
        lines.append(f"  Mean Shift Index     : {s_mean:.4f}")
        lines.append(f"  Peak Shift Index     : {s_max:.4f}  → {s_label}")
        if s_max >= HIGH_SHIFT:
            lines.append(f"  → The structure's vibration mode pattern has deviated significantly")
            lines.append(f"    from its baseline, suggesting possible stiffness reduction or cracking.")
    if dynamics_col:
        d_mean = df[dynamics_col].mean()
        lines.append(f"  Structural Dynamics  : {d_mean:.4f}  → {'STIFFNESS CHANGE DETECTED' if d_mean >= 0.5 else 'Nominal'}")
    if cluster_col:
        mode_cluster = int(df[cluster_col].mode()[0])
        cluster_desc = {0: "Normal Baseline", 1: "Intermediate / Active Load", 2: "Altered Structural Dynamics ⚠"}
        lines.append(f"  Dominant Oper. Mode  : State {mode_cluster} ({cluster_desc.get(mode_cluster, 'Unknown')})")

    # ─── Supporting Sensor Context ──────────────────────────────────────────
    sensor_context = {}
    for kw, label in [('accel', 'Acceleration'), ('strain', 'Strain'),
                      ('deflection', 'Deflection'), ('temp', 'Temperature'),
                      ('rms', 'Vibration RMS')]:
        matches = [c for c in df.columns if kw in c.lower() and pd.api.types.is_numeric_dtype(df[c])]
        if matches:
            col = matches[0]
            sensor_context[label] = f"Mean={df[col].mean():.4f}  Max={df[col].max():.4f}"

    if sensor_context:
        lines.append(f"\n[SUPPORTING SENSOR SIGNALS]")
        for label, vals in sensor_context.items():
            lines.append(f"  {label:<20} : {vals}")

    # ─── Engineering Recommendation ─────────────────────────────────────────
    lines.append(f"\n{'─' * 60}")
    lines.append("  ENGINEERING RECOMMENDATION")
    lines.append(f"{'─' * 60}")
    if risk_col and df[risk_col].max() >= CRITICAL_RISK:
        lines.append("  ⛔ IMMEDIATE ACTION REQUIRED")
        lines.append("  Predicted risk exceeds CRITICAL threshold (0.75).")
        lines.append("  → Schedule physical structural inspection within 72 hours.")
        lines.append("  → Deploy additional sensors at high-anomaly zones.")
        lines.append("  → Review recent load history and environmental events.")
    elif risk_col and df[risk_col].max() >= HIGH_RISK:
        lines.append("  ⚠ ELEVATED RISK — PRIORITIZED MAINTENANCE")
        lines.append("  → Schedule detailed inspection within the next 2 weeks.")
        lines.append("  → Review anomaly timeline for pattern clusters.")
    else:
        lines.append("  ✓ ROUTINE MONITORING")
        lines.append("  → Continue standard inspection schedule.")
        lines.append("  → Monitor Behavioral Shift Index for upward trends.")

    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print(explain_high_risk("B001"))
