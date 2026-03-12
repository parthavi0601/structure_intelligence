"""
tools/maintenance_prioritizer.py
=================================
Tool 3: Maintenance Prioritization Tool
Ranks all monitored infrastructure assets by Predicted_Risk_Score
and outputs an ordered maintenance schedule with urgency levels.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import (
    PROCESSED_DIR, PREFERRED_DATASETS,
    CRITICAL_RISK, HIGH_RISK
)


def prioritize_maintenance(query: str = "") -> str:
    """
    Tool 3: Maintenance Prioritization Tool
    Ranks all infrastructure assets by predicted failure risk score and
    provides a maintenance action schedule ordered by urgency.

    Args:
        query: Optional hint (e.g., "this month", "bridges"). Currently informational.

    Returns:
        An ordered maintenance priority list with urgency levels.
    """
    asset_rows = []

    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if not fpath.exists():
            continue
        try:
            df = pd.read_parquet(fpath)
        except Exception:
            continue

        risk_col    = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
        anomaly_col = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
        shift_col   = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
        alert_col   = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)

        if risk_col is None:
            continue

        # Try to group by asset ID
        id_col = next((c for c in ['bridge_id', 'Bridge_ID', 'sensor_id', 'test_id'] if c in df.columns), None)

        if id_col:
            groups = df.groupby(id_col)
            for asset_id, group in groups:
                asset_rows.append({
                    "Asset ID":      str(asset_id),
                    "Dataset":       fname.replace(".parquet", ""),
                    "Mean Risk":     round(group[risk_col].mean(), 4),
                    "Peak Risk":     round(group[risk_col].max(), 4),
                    "Mean Anomaly":  round(group[anomaly_col].mean(), 4) if anomaly_col else None,
                    "Mean Shift":    round(group[shift_col].mean(), 4) if shift_col else None,
                    "Alert Events":  int(group[alert_col].sum()) if alert_col else 0,
                    "Readings":      len(group),
                })
        else:
            # Treat whole dataset as one asset
            asset_rows.append({
                "Asset ID":     fname.replace("_behavior.parquet", "").replace(".parquet", ""),
                "Dataset":      fname.replace(".parquet", ""),
                "Mean Risk":    round(df[risk_col].mean(), 4),
                "Peak Risk":    round(df[risk_col].max(), 4),
                "Mean Anomaly": round(df[anomaly_col].mean(), 4) if anomaly_col else None,
                "Mean Shift":   round(df[shift_col].mean(), 4) if shift_col else None,
                "Alert Events": int(df[alert_col].sum()) if alert_col else 0,
                "Readings":     len(df),
            })

    if not asset_rows:
        return "ERROR: No risk score data found across any processed datasets. Ensure run_risk_prediction.py has been executed."

    # Sort by Peak Risk descending
    asset_rows.sort(key=lambda x: x["Peak Risk"], reverse=True)

    lines = ["=" * 65]
    lines.append("  MAINTENANCE PRIORITIZATION REPORT")
    lines.append("=" * 65)

    critical = [a for a in asset_rows if a["Peak Risk"] >= CRITICAL_RISK]
    high     = [a for a in asset_rows if HIGH_RISK <= a["Peak Risk"] < CRITICAL_RISK]
    routine  = [a for a in asset_rows if a["Peak Risk"] < HIGH_RISK]

    def _render_tier(tier_label: str, icon: str, assets: list, action: str) -> list:
        if not assets:
            return []
        out = [f"\n{icon}  {tier_label}  ({len(assets)} asset(s))", f"    Recommended Action: {action}", ""]
        for rank, a in enumerate(assets, 1):
            out.append(f"  Rank {rank:02d}  | {a['Asset ID']:<25} | Peak Risk: {a['Peak Risk']:.4f}")
            out.append(f"          | Dataset: {a['Dataset']}")
            if a["Mean Anomaly"] is not None:
                out.append(f"          | Mean Anomaly Score: {a['Mean Anomaly']:.4f}")
            if a["Mean Shift"] is not None:
                out.append(f"          | Mean Behavioral Shift: {a['Mean Shift']:.4f}")
            if a["Alert Events"]:
                out.append(f"          | Anomaly Alert Events: {a['Alert Events']}")
            out.append("")
        return out

    lines += _render_tier(
        "TIER 1 — CRITICAL RISK (Peak Risk ≥ 0.75)", "⛔",
        critical,
        "Immediate physical inspection within 72 hours. Deploy emergency monitoring."
    )
    lines += _render_tier(
        "TIER 2 — HIGH RISK (0.50 ≤ Peak Risk < 0.75)", "⚠",
        high,
        "Schedule detailed inspection within 2 weeks. Review failure risk trends."
    )
    lines += _render_tier(
        "TIER 3 — ROUTINE MAINTENANCE (Peak Risk < 0.50)", "✓",
        routine,
        "Maintain standard inspection schedule. Monitor behavioral shift trends."
    )

    lines.append(f"{'─' * 65}")
    lines.append(f"  Total Assets Ranked : {len(asset_rows)}")
    lines.append(f"  Critical            : {len(critical)}")
    lines.append(f"  High Priority       : {len(high)}")
    lines.append(f"  Routine             : {len(routine)}")
    lines.append("=" * 65)

    return "\n".join(lines)


if __name__ == "__main__":
    print(prioritize_maintenance())
