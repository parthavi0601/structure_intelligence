"""
validate.py
===========
Post-pipeline sanity checks — run after run_pipeline.py completes.

Checks:
  1. All 5 output parquet files exist
  2. Zero NaN values in each output
  3. Non-empty (rows > 0, cols > 0)
  4. Numeric column value ranges are plausible after normalization

Usage:
    python pipeline/validate.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import OUTPUT_FILES, LOGS_DIR
from pipeline.utils import get_logger

log = get_logger("validate", LOGS_DIR)

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def check(condition: bool, message: str) -> str:
    status = PASS if condition else FAIL
    log.info(f"  {status}  {message}")
    return status


def validate_dataset(name: str, path: Path) -> dict:
    results = {"dataset": name, "checks": []}
    add = results["checks"].append

    # 1. File exists
    add(check(path.exists(), f"Output file exists: {path.name}"))
    if not path.exists():
        return results

    # 2. Loads without error
    try:
        df = pd.read_parquet(path, engine="pyarrow")
    except Exception as e:
        add(check(False, f"Load parquet failed: {e}"))
        return results

    add(check(True, f"Parquet loaded OK"))

    # 3. Non-empty
    add(check(df.shape[0] > 0, f"Non-empty rows: {df.shape[0]:,}"))
    add(check(df.shape[1] > 0, f"Non-empty cols: {df.shape[1]:,}"))

    # 4. Zero NaN
    total_nan = df.isna().sum().sum()
    add(check(total_nan == 0, f"Zero NaN values (found {total_nan})"))

    # 5. Numeric range sanity
    num_cols  = df.select_dtypes(include="number").columns.tolist()
    # Exclude binary int8 cols and engineered flags
    scale_cols = [c for c in num_cols if df[c].dtype != "int8"
                  and c not in {"window_start", "test_id"}]

    if scale_cols:
        sample      = df[scale_cols].describe()
        max_abs_val = df[scale_cols].abs().max().max()
        # After StandardScaler values should mostly be in [-10, 10]
        # After MinMaxScaler values should be in [0, 1]
        reasonable  = max_abs_val < 1000          # exclude obviously blown-up values
        add(check(reasonable, f"Max abs numeric value is reasonable ({max_abs_val:.3f} < 1000)"))

    # 6. Engineered features present
    feat_checks = {
        "sensor_fusion":  lambda d: any("_rmean_" in c for c in d.columns),
        "behaviour":      lambda d: any("_rms" in c for c in d.columns),
        "anomaly":        lambda d: any(c.startswith("pca_") for c in d.columns),
        "failure":        lambda d: any("_lag" in c for c in d.columns),
        "digital_twin":   lambda d: any("SHI_lag" in c for c in d.columns),
    }
    if name in feat_checks:
        has_feats = feat_checks[name](df)
        add(check(has_feats, f"Engineered feature columns present"))

    log.info(f"  Shape: {df.shape} | dtypes: {dict(df.dtypes.value_counts())}")
    return results


def main():
    log.info("=" * 60)
    log.info("  PIPELINE VALIDATION REPORT")
    log.info("=" * 60)

    all_pass = True
    for name, path in OUTPUT_FILES.items():
        log.info(f"\n[{name.upper()}]")
        r = validate_dataset(name, path)
        failed = [c for c in r["checks"] if FAIL in c]
        if failed:
            all_pass = False

    log.info("\n" + "=" * 60)
    if all_pass:
        log.info("  ✅ ALL CHECKS PASSED — pipeline output is valid!")
    else:
        log.info("  ❌ SOME CHECKS FAILED — review logs above")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
