"""
run_pipeline.py
===============
Main orchestrator — runs the full data processing pipeline for all 5 datasets.

Usage:
    python pipeline/run_pipeline.py

Outputs in  processed/
    sensor_fusion.parquet
    behaviour.parquet
    anomaly.parquet
    failure_prediction.parquet
    digital_twin.parquet

Fitted scalers saved in  processed/scalers/
"""
import sys
import time
import traceback
from pathlib import Path

# Make sure project root is on the Python path when run directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import OUTPUT_FILES, PROCESSED_DIR, SCALERS_DIR, LOGS_DIR
from pipeline.utils import get_logger, save_parquet, save_report, df_report

from pipeline.loaders import (
    load_sensor_fusion, load_behaviour, load_anomaly,
    load_failure, load_digital_twin,
)
from pipeline.processors import clean, transform, engineer_features


log = get_logger("run_pipeline", LOGS_DIR)


def run_single(name: str, loader_fn, fit: bool = True) -> dict:
    """Run load → clean → transform → engineer → save for one dataset."""
    result = {"dataset": name, "status": "pending", "shape": None, "elapsed_s": None}
    t0 = time.perf_counter()
    try:
        log.info(f"\n{'='*60}")
        log.info(f"  PROCESSING DATASET: {name.upper()}")
        log.info(f"{'='*60}")

        # ── Load ──────────────────────────────────────────────────────────────
        df = loader_fn()
        df_report(df, f"{name} [loaded]", log)

        # ── Clean ─────────────────────────────────────────────────────────────
        df = clean(df, dataset_name=name)

        # ── Transform ─────────────────────────────────────────────────────────
        df = transform(df, dataset_name=name, fit=fit, scaler_dir=SCALERS_DIR)

        # ── Feature Engineering ───────────────────────────────────────────────
        df = engineer_features(df, dataset_name=name, fit=fit, scaler_dir=SCALERS_DIR)

        # ── Final NaN sweep ───────────────────────────────────────────────────
        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].ffill().bfill().fillna(0)

        # ── Save ──────────────────────────────────────────────────────────────
        out_path = OUTPUT_FILES[name]
        save_parquet(df, out_path, log)

        result["status"] = "✅ SUCCESS"
        result["shape"]  = list(df.shape)
        log.info(f"  → {name} complete: shape={df.shape}")

    except Exception as e:
        result["status"] = f"❌ FAILED: {e}"
        log.error(f"  [{name}] FAILED: {e}")
        log.error(traceback.format_exc())

    result["elapsed_s"] = round(time.perf_counter() - t0, 2)
    return result


def main():
    log.info("=" * 60)
    log.info("  STRUCTURE INTELLIGENCE — DATA PIPELINE")
    log.info("=" * 60)

    # Ensure output directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SCALERS_DIR.mkdir(parents=True, exist_ok=True)

    pipeline_tasks = [
        ("sensor_fusion",  load_sensor_fusion),
        ("behaviour",      load_behaviour),
        ("anomaly",        load_anomaly),
        ("failure",        load_failure),
        ("digital_twin",   load_digital_twin),
    ]

    summary = []
    total_start = time.perf_counter()

    for name, loader_fn in pipeline_tasks:
        report = run_single(name, loader_fn, fit=True)
        summary.append(report)

    # ── Print Summary Table ────────────────────────────────────────────────────
    total_elapsed = round(time.perf_counter() - total_start, 2)
    log.info("\n" + "=" * 60)
    log.info("  PIPELINE SUMMARY")
    log.info("=" * 60)
    log.info(f"  {'Dataset':<20} {'Status':<20} {'Shape':<20} {'Time(s)'}")
    log.info(f"  {'-'*20} {'-'*20} {'-'*20} {'-'*10}")
    for r in summary:
        shape_str = str(r["shape"]) if r["shape"] else "N/A"
        log.info(f"  {r['dataset']:<20} {r['status']:<20} {shape_str:<20} {r['elapsed_s']}s")
    log.info(f"\n  Total time: {total_elapsed}s")
    log.info("=" * 60)

    # ── Save JSON report ───────────────────────────────────────────────────────
    save_report({"summary": summary, "total_elapsed_s": total_elapsed},
                LOGS_DIR / "pipeline_report.json")
    log.info(f"Report saved → {LOGS_DIR / 'pipeline_report.json'}")


if __name__ == "__main__":
    main()
