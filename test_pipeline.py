"""Quick diagnostic: test each dataset independently and print results."""
import sys
import warnings
import traceback
warnings.filterwarnings("ignore")

sys.path.insert(0, ".")

from pipeline.loaders import (
    load_sensor_fusion, load_behaviour, load_anomaly,
    load_failure, load_digital_twin
)
from pipeline.processors import clean, transform, engineer_features

tasks = [
    ("sensor_fusion", load_sensor_fusion),
    ("behaviour",     load_behaviour),
    ("anomaly",       load_anomaly),
    ("failure",       load_failure),
    ("digital_twin",  load_digital_twin),
]

all_ok = True
for name, loader in tasks:
    print(f"\n--- {name} ---", flush=True)
    try:
        df = loader()
        print(f"  Loaded:      {df.shape}", flush=True)
        df = clean(df, name)
        print(f"  Cleaned:     {df.shape}", flush=True)
        df = transform(df, name)
        print(f"  Transformed: {df.shape}", flush=True)
        df = engineer_features(df, name)
        print(f"  Engineered:  {df.shape}", flush=True)
        nc = df.select_dtypes(include="number").columns
        df[nc] = df[nc].ffill().bfill().fillna(0)
        print(f"  FINAL: shape={df.shape}, nan={df.isna().sum().sum()}", flush=True)
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        traceback.print_exc()
        all_ok = False

print("\n" + ("=== ALL OK ===" if all_ok else "=== SOME FAILED ==="), flush=True)
sys.exit(0 if all_ok else 1)
