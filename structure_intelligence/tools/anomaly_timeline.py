"""
tools/anomaly_timeline.py
=========================
Tool 4: Anomaly Timeline Inspector
Detects and summarizes all timestamps/records where anomaly alert flags
were triggered, providing structural event context for engineers.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import PROCESSED_DIR, PREFERRED_DATASETS, HIGH_ANOMALY


def inspect_anomaly_timeline(query: str = "") -> str:
    """
    Tool 4: Anomaly Timeline Inspector
    Scans all processed datasets for anomaly alert events and returns
    a structured timeline of structural events with context.

    Args:
        query: Optional asset or dataset filter hint.

    Returns:
        A formatted timeline of anomaly events with sensor context.
    """
    query_lower = query.lower().strip()
    lines = ["=" * 65]
    lines.append("  ANOMALY EVENT TIMELINE REPORT")
    lines.append("=" * 65)

    total_events = 0
    found_any = False

    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if not fpath.exists():
            continue

        # Apply query filter on filename
        if query_lower and query_lower not in fname.lower() and query_lower not in ["all", "latest", "recent", "show"]:
            # Try to match — if query is a broad word like "anomaly" or "bridge", don't filter by dataset name
            generic_queries = ["anomaly", "anomalies", "events", "bridge", "structure", "latest", "recent", "month", "this"]
            if not any(gq in query_lower for gq in generic_queries):
                if query_lower not in fname.lower():
                    continue

        try:
            df = pd.read_parquet(fpath)
        except Exception:
            continue

        alert_col   = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)
        anomaly_col = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
        shift_col   = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
        risk_col    = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
        time_col    = next((c for c in df.columns if any(t in c.lower() for t in ['timestamp', 'time', 'time_s', 'time_step'])), None)
        id_col      = next((c for c in ['bridge_id', 'Bridge_ID', 'sensor_id', 'test_id'] if c in df.columns), None)

        if alert_col is None and anomaly_col is None:
            continue

        found_any = True

        # Get flagged events — use explicit alerts if available, else threshold-based
        if alert_col and df[alert_col].sum() > 0:
            events = df[df[alert_col] == 1].copy()
            event_source = "Anomaly Alert Flag"
        elif anomaly_col:
            events = df[df[anomaly_col] >= HIGH_ANOMALY].copy()
            event_source = f"Anomaly Score ≥ {HIGH_ANOMALY}"
        else:
            continue

        n_events = len(events)
        total_events += n_events

        lines.append(f"\nDataset: {fname.replace('.parquet','')}")
        lines.append(f"  Event Source   : {event_source}")
        lines.append(f"  Total Events   : {n_events}")

        if n_events == 0:
            lines.append("  → No anomaly events detected.")
            continue

        # Build event table — show up to 15 most recent/severe events
        if anomaly_col:
            events = events.sort_values(anomaly_col, ascending=False)
        display_count = min(n_events, 15)
        shown = events.head(display_count)

        lines.append(f"\n  Top {display_count} Events (sorted by severity):")
        lines.append(f"  {'Index':<8} {'Time/ID':<20} {'Anomaly':>9} {'Risk':>8} {'Shift':>8}")
        lines.append(f"  {'─'*8} {'─'*20} {'─'*9} {'─'*8} {'─'*8}")

        for idx, row in shown.iterrows():
            time_val   = str(row[time_col])[:18] if time_col and time_col in row.index else str(idx)
            if id_col:
                time_val = f"{row[id_col]}@{time_val}"
            a_val = f"{row[anomaly_col]:.4f}" if anomaly_col and anomaly_col in row.index else "  N/A "
            r_val = f"{row[risk_col]:.4f}"    if risk_col    and risk_col    in row.index else "  N/A "
            s_val = f"{row[shift_col]:.4f}"   if shift_col   and shift_col   in row.index else "  N/A "
            lines.append(f"  {str(idx):<8} {time_val:<20} {a_val:>9} {r_val:>8} {s_val:>8}")

        if n_events > display_count:
            lines.append(f"\n  ... and {n_events - display_count} more events (showing top {display_count} by severity)")

        # Cluster analysis: any clusters of back-to-back events?
        event_indices = list(events.index)
        if len(event_indices) > 1:
            clusters = []
            current_cluster = [event_indices[0]]
            for i in range(1, len(event_indices)):
                if event_indices[i] - event_indices[i-1] <= 5:  # within 5 rows = consecutive burst
                    current_cluster.append(event_indices[i])
                else:
                    if len(current_cluster) > 1:
                        clusters.append(current_cluster)
                    current_cluster = [event_indices[i]]
            if len(current_cluster) > 1:
                clusters.append(current_cluster)
            if clusters:
                lines.append(f"\n  Sustained Event Clusters Detected: {len(clusters)}")
                for cl in clusters[:3]:
                    lines.append(f"    Cluster at rows {cl[0]}–{cl[-1]}  ({len(cl)} consecutive events)")

        # Peak anomaly context
        if anomaly_col:
            peak_row = events.loc[events[anomaly_col].idxmax()]
            lines.append(f"\n  Highest Severity Event:")
            lines.append(f"    Anomaly Score    : {peak_row[anomaly_col]:.4f}")
            if risk_col:
                lines.append(f"    Risk Score       : {peak_row[risk_col]:.4f}")
            if shift_col:
                lines.append(f"    Behavioral Shift : {peak_row[shift_col]:.4f}")

    if not found_any:
        lines.append("\nNo anomaly or alert flag data found in processed datasets.")
        lines.append("Ensure run_anomaly_detection.py has been executed before querying the timeline.")

    lines.append(f"\n{'─' * 65}")
    lines.append(f"  TOTAL ANOMALY EVENTS IDENTIFIED: {total_events}")
    if total_events > 0:
        lines.append("  Recommendation: Review sustained event clusters first.")
        lines.append("  Cross-reference with Maintenance Prioritization Tool.")
    lines.append("=" * 65)
    return "\n".join(lines)


if __name__ == "__main__":
    print(inspect_anomaly_timeline())
