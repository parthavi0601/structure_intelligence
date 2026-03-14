"""
tools/health_analyzer.py
========================
Tool 1: Infrastructure Health Analyzer
Reads all processed *_behavior.parquet files and returns a structured
summary of overall infrastructure health across all monitored assets.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Allow import from parent directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import (
    PROCESSED_DIR, PREFERRED_DATASETS,
    CRITICAL_RISK, HIGH_RISK, HIGH_ANOMALY, HIGH_SHIFT
)


def _load_all_datasets() -> list[tuple[str, pd.DataFrame]]:
    """Load all available *_behavior.parquet files."""
    datasets = []
    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if fpath.exists():
            try:
                df = pd.read_parquet(fpath)
                datasets.append((fname.replace(".parquet", ""), df))
            except Exception:
                pass
    # Fallback: any remaining parquet
    if not datasets:
        for f in PROCESSED_DIR.glob("*.parquet"):
            try:
                df = pd.read_parquet(f)
                datasets.append((f.stem, df))
            except Exception:
                pass
    return datasets


def analyze_infrastructure_health(query: str = "") -> str:
    """
    Tool 1: Infrastructure Health Analyzer
    Reads all processed parquet datasets and returns a comprehensive
    structural health summary with key AI-computed metrics.

    Args:
        query: Optional filter hint (e.g., asset name). Ignored in aggregate mode.

    Returns:
        A formatted engineering health report string.
    """
    datasets = _load_all_datasets()
    if not datasets:
        return "ERROR: No processed parquet files found in the processed/ directory. Ensure the pipeline has been run."

    lines = ["=" * 60]
    lines.append("  INFRASTRUCTURE HEALTH ANALYSIS REPORT")
    lines.append("=" * 60)

    total_records = 0
    all_anomaly_scores = []
    all_risk_scores = []
    all_shift_indices = []
    all_dynamics_scores = []
    dataset_summaries = []

    for name, df in datasets:
        n = len(df)
        total_records += n

        # Collect global stats
        anomaly_col    = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
        risk_col       = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
        shift_col      = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
        dynamics_col   = next((c for c in df.columns if 'Structural_Dynamics_Score' in c), None)
        alert_col      = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)
        cluster_col    = next((c for c in df.columns if 'Behavioral_State_Cluster' in c), None)

        summary = {
            "name":          name,
            "records":       n,
            "mean_anomaly":  df[anomaly_col].mean()   if anomaly_col   else None,
            "max_anomaly":   df[anomaly_col].max()    if anomaly_col   else None,
            "mean_risk":     df[risk_col].mean()      if risk_col      else None,
            "max_risk":      df[risk_col].max()       if risk_col      else None,
            "mean_shift":    df[shift_col].mean()     if shift_col     else None,
            "mean_dynamics": df[dynamics_col].mean()  if dynamics_col  else None,
            "alert_count":   int(df[alert_col].sum()) if alert_col     else 0,
            "modal_cluster": int(df[cluster_col].mode()[0]) if cluster_col else None,
        }

        if anomaly_col:   all_anomaly_scores.extend(df[anomaly_col].dropna().tolist())
        if risk_col:      all_risk_scores.extend(df[risk_col].dropna().tolist())
        if shift_col:     all_shift_indices.extend(df[shift_col].dropna().tolist())
        if dynamics_col:  all_dynamics_scores.extend(df[dynamics_col].dropna().tolist())

        dataset_summaries.append(summary)

    # ─── Fleet-Level Summary ─────────────────────────────────────────────────
    lines.append(f"\nDatasets Analyzed: {len(datasets)}")
    lines.append(f"Total Readings:    {total_records:,}")

    if all_anomaly_scores:
        mean_a = np.mean(all_anomaly_scores)
        max_a  = np.max(all_anomaly_scores)
        status = "ELEVATED" if max_a >= HIGH_ANOMALY else "NORMAL"
        lines.append(f"\n[ANOMALY DETECTION]")
        lines.append(f"  Fleet Mean Anomaly Score : {mean_a:.4f}")
        lines.append(f"  Fleet Max Anomaly Spike  : {max_a:.4f}  [{status}]")

    if all_risk_scores:
        mean_r = np.mean(all_risk_scores)
        max_r  = np.max(all_risk_scores)
        risk_label = "CRITICAL" if max_r >= CRITICAL_RISK else ("HIGH" if max_r >= HIGH_RISK else "LOW")
        lines.append(f"\n[FAILURE RISK]")
        lines.append(f"  Fleet Mean Risk Score    : {mean_r:.4f}")
        lines.append(f"  Fleet Max Risk Score     : {max_r:.4f}  [{risk_label}]")

    if all_shift_indices:
        mean_s = np.mean(all_shift_indices)
        lines.append(f"\n[BEHAVIORAL ANALYSIS]")
        lines.append(f"  Fleet Mean Shift Index   : {mean_s:.4f}")
        lines.append(f"  Fleet Mean Dynamics Score: {np.mean(all_dynamics_scores):.4f}" if all_dynamics_scores else "")

    # ─── Per-Dataset Breakdown ───────────────────────────────────────────────
    lines.append(f"\n{'─' * 60}")
    lines.append("  PER-DATASET BREAKDOWN")
    lines.append(f"{'─' * 60}")

    for s in dataset_summaries:
        lines.append(f"\nDataset : {s['name']}")
        lines.append(f"  Records                 : {s['records']:,}")
        if s['mean_anomaly'] is not None:
            a_flag = " ⚠ HIGH" if s['max_anomaly'] >= HIGH_ANOMALY else ""
            lines.append(f"  Mean Anomaly Score      : {s['mean_anomaly']:.4f}  (Max: {s['max_anomaly']:.4f}{a_flag})")
        if s['mean_risk'] is not None:
            r_label = " ⚠ CRITICAL" if s['max_risk'] >= CRITICAL_RISK else (" ⚠ HIGH" if s['max_risk'] >= HIGH_RISK else "")
            lines.append(f"  Mean Risk Score         : {s['mean_risk']:.4f}  (Max: {s['max_risk']:.4f}{r_label})")
        if s['mean_shift'] is not None:
            lines.append(f"  Mean Behavioral Shift   : {s['mean_shift']:.4f}")
        if s['mean_dynamics'] is not None:
            lines.append(f"  Mean Dynamics Score     : {s['mean_dynamics']:.4f}")
        if s['alert_count']:
            lines.append(f"  Anomaly Alert Flags     : {s['alert_count']} events")
        if s['modal_cluster'] is not None:
            cluster_desc = {0: "Normal Baseline", 1: "Intermediate/Active Load", 2: "Altered Dynamics"}
            lines.append(f"  Dominant Behavioral Mode: State {s['modal_cluster']} ({cluster_desc.get(s['modal_cluster'], 'Unknown')})")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print(analyze_infrastructure_health())
