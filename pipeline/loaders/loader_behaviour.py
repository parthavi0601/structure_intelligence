"""
loader_behaviour.py
===================
Loads Dataset 2: Bridge vibration TXT files (test1.txt … test8.txt).
Each file is tab-separated with a 9-line header.
Returns one concatenated DataFrame with columns:
  time_s, ch1_g, ch2_g, ch3_g, ch4_g, ch5_g, test_id
"""
import pandas as pd
import numpy as np
from pathlib import Path

from pipeline.utils import get_logger, df_report
from pipeline.config import PATHS, LOGS_DIR


HEADER_ROWS = 9          # lines to skip before data starts
CHANNEL_NAMES = ["ch1_g", "ch2_g", "ch3_g", "ch4_g", "ch5_g"]


def _parse_single_txt(filepath: Path, test_id: str) -> pd.DataFrame:
    """Parse one QuickDAQ .txt file into a tidy DataFrame."""
    df = pd.read_csv(
        filepath,
        sep=r"\t",
        skiprows=HEADER_ROWS,
        header=None,
        engine="python",
        names=["time_s"] + CHANNEL_NAMES,
        na_values=["", " ", "NaN", "nan"],
    )

    # strip scientific notation / whitespace from all columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    df = df.apply(pd.to_numeric, errors="coerce")

    df["test_id"] = test_id
    return df


def load_behaviour(path: Path = None) -> pd.DataFrame:
    log = get_logger("loader.behaviour", LOGS_DIR)
    directory = Path(path or PATHS["behaviour"])
    log.info(f"Loading behaviour vibration files from: {directory}")

    txt_files = sorted(directory.glob("test*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No test*.txt files found in {directory}")

    frames = []
    for fpath in txt_files:
        test_id = fpath.stem        # "test1", "test2", …
        log.info(f"  Parsing {fpath.name} …")
        df = _parse_single_txt(fpath, test_id)
        frames.append(df)
        log.info(f"    → {df.shape[0]} rows")

    combined = pd.concat(frames, ignore_index=True)

    # Cast channels to float32
    for col in CHANNEL_NAMES:
        combined[col] = combined[col].astype("float32")

    df_report(combined, "behaviour [raw]", log)
    return combined
