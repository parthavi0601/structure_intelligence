"""
tools/health_summary.py
========================
Tool 5: Structural Health Summary Generator
Produces a comprehensive engineering report covering anomaly trends,
behavioral drift, risk levels, and recommended actions per asset.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import (
    PROCESSED_DIR, PREFERRED_DATASETS,
    CRITICAL_RISK, HIGH_RISK, HIGH_ANOMALY, HIGH_SHIFT
)


def generate_health_summary(query: str = "") -> str:
    """
    Tool 5: Structural Health Summary Generator
    Produces a concise, structured engineering health report for all
    monitored infrastructure assets, combining all AI module outputs.

    Args:
        query: Optional focus (e.g., a bridge name, "vibration", "all"). Currently informational.

    Returns:
        A formatted structural health summary report string.
    """
    lines = ["=" * 65]
    lines.append("  STRUCTURAL HEALTH SUMMARY — COMPLETE ENGINEERING REPORT")
    lines.append("=" * 65)

    all_records = []
    dataset_count = 0

    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if not fpath.exists():
            continue
        try:
            df = pd.read_parquet(fpath)
        except Exception:
            continue

        dataset_count += 1
        id_col      = next((c for c in ['bridge_id', 'Bridge_ID', 'sensor_id', 'test_id'] if c in df.columns), None)
        anomaly_col = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
        alert_col   = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)
        risk_col    = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
        shift_col   = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
        dynamics_col= next((c for c in df.columns if 'Structural_Dynamics_Score' in c), None)
        cluster_col = next((c for c in df.columns if 'Behavioral_State_Cluster' in c), None)

        groups = [(fname.replace(".parquet",""), df)] if not id_col else \
                 [(asset_id, grp) for asset_id, grp in df.groupby(id_col)]

        for asset_id, grp in groups:
            n = len(grp)

            # Trend: compare first third vs last third
            def trend(col):
                if col is None or col not in grp.columns: return None
                first = grp[col].iloc[:n//3].mean() if n >= 3 else None
                last  = grp[col].iloc[-n//3:].mean() if n >= 3 else None
                if first is None or last is None: return "N/A"
                delta = last - first
                return f"{'↑' if delta > 0.03 else ('↓' if delta < -0.03 else '→')}  ({delta:+.4f})"

            record = {
                "asset":          str(asset_id),
                "dataset":        fname.replace(".parquet",""),
                "readings":       n,
                "mean_anomaly":   grp[anomaly_col].mean()    if anomaly_col   else None,
                "max_anomaly":    grp[anomaly_col].max()     if anomaly_col   else None,
                "anomaly_trend":  trend(anomaly_col),
                "alert_count":    int(grp[alert_col].sum())  if alert_col     else 0,
                "mean_risk":      grp[risk_col].mean()       if risk_col      else None,
                "max_risk":       grp[risk_col].max()        if risk_col      else None,
                "risk_trend":     trend(risk_col),
                "mean_shift":     grp[shift_col].mean()      if shift_col     else None,
                "shift_trend":    trend(shift_col),
                "mean_dynamics":  grp[dynamics_col].mean()   if dynamics_col  else None,
                "modal_state":    int(grp[cluster_col].mode()[0]) if cluster_col else None,
            }
            all_records.append(record)

    if not all_records:
        return "ERROR: No processed datasets found. Run the full analysis pipeline before querying the health summary."

    # Sort by max_risk descending (highest risk first)
    all_records.sort(key=lambda r: (r["max_risk"] or 0), reverse=True)

    lines.append(f"\nDatasets Loaded  : {dataset_count}")
    lines.append(f"Assets Analyzed  : {len(all_records)}")
    lines.append(f"{'─' * 65}")

    cluster_desc = {0: "State 0: Normal Baseline", 1: "State 1: Intermediate/Active Load", 2: "State 2: Altered Dynamics ⚠"}

    for record in all_records:
        # Determine overall health status
        max_r = record["max_risk"] or 0
        max_a = record["max_anomaly"] or 0
        max_s = record["mean_shift"] or 0
        if max_r >= CRITICAL_RISK or max_a >= 0.85:
            health_status = "⛔ CRITICAL"
        elif max_r >= HIGH_RISK or max_a >= HIGH_ANOMALY or max_s >= HIGH_SHIFT:
            health_status = "⚠  HIGH RISK"
        else:
            health_status = "✓  HEALTHY"

        lines.append(f"\n╔═ Asset: {record['asset']}")
        lines.append(f"║  Dataset      : {record['dataset']}")
        lines.append(f"║  Readings     : {record['readings']:,}")
        lines.append(f"║  HEALTH STATUS: {health_status}")
        lines.append(f"╠──── ANOMALY DETECTION ─────────────────────────────────────")
        if record["mean_anomaly"] is not None:
            lines.append(f"║  Mean Anomaly Score   : {record['mean_anomaly']:.4f}  (Peak: {record['max_anomaly']:.4f})")
            lines.append(f"║  Anomaly Trend        : {record['anomaly_trend']}")
            lines.append(f"║  Alert Flag Events    : {record['alert_count']}")
        else:
            lines.append(f"║  → No anomaly score data available")
        lines.append(f"╠──── BEHAVIORAL DRIFT ──────────────────────────────────────")
        if record["mean_shift"] is not None:
            lines.append(f"║  Behavioral Shift Idx : {record['mean_shift']:.4f}  Trend: {record['shift_trend']}")
            lines.append(f"║  Structural Dynamics  : {record['mean_dynamics']:.4f}" if record["mean_dynamics"] else "║  Structural Dynamics  : N/A")
            lines.append(f"║  Modal State          : {cluster_desc.get(record['modal_state'], 'N/A')}")
        else:
            lines.append(f"║  → No behavioral shift data available")
        lines.append(f"╠──── FAILURE RISK ──────────────────────────────────────────")
        if record["mean_risk"] is not None:
            lines.append(f"║  Mean Risk Score      : {record['mean_risk']:.4f}  (Peak: {record['max_risk']:.4f})")
            lines.append(f"║  Risk Trend           : {record['risk_trend']}")
        else:
            lines.append(f"║  → No risk prediction data available")
        lines.append(f"╠──── RECOMMENDATION ────────────────────────────────────────")
        if max_r >= CRITICAL_RISK:
            lines.append(f"║  → ⛔ IMMEDIATE INSPECTION within 72 hours.")
            lines.append(f"║     Deploy emergency monitoring. Review traffic loading.")
        elif max_r >= HIGH_RISK or max_a >= HIGH_ANOMALY:
            lines.append(f"║  → ⚠ Schedule detailed inspection within 2 weeks.")
            lines.append(f"║     Analyze anomaly timeline for event clusters.")
        elif max_s >= HIGH_SHIFT:
            lines.append(f"║  → Monitor closely. Behavioral shift pattern warrants")
            lines.append(f"║     detailed vibration analysis within 30 days.")
        else:
            lines.append(f"║  → ✓ Continue standard monitoring schedule.")
        lines.append(f"╚═{'═'*55}")

    # Fleet-level aggregate
    all_risks    = [r["max_risk"] or 0 for r in all_records]
    all_anomalies = [r["max_anomaly"] or 0 for r in all_records]
    lines.append(f"\n{'─' * 65}")
    lines.append(f"  FLEET SUMMARY")
    lines.append(f"{'─' * 65}")
    lines.append(f"  Critical Assets      : {sum(1 for r in all_risks if r >= CRITICAL_RISK)}/{len(all_records)}")
    lines.append(f"  High Risk Assets     : {sum(1 for r in all_risks if HIGH_RISK <= r < CRITICAL_RISK)}/{len(all_records)}")
    lines.append(f"  Healthy Assets       : {sum(1 for r in all_risks if r < HIGH_RISK)}/{len(all_records)}")
    lines.append(f"  Highest Fleet Risk   : {max(all_risks):.4f}")
    lines.append(f"  Highest Fleet Anomaly: {max(all_anomalies):.4f}")
    lines.append("=" * 65)
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_health_summary())
