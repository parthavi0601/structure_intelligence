"""
embeddings/build_vectorstore.py
================================
Embeddings Pipeline: Builds a FAISS vector store from structural data summaries.
Run this script once (or after data updates) to build/refresh the vector index.

Usage:
    python embeddings/build_vectorstore.py

Output:
    processed/faiss_index/index.faiss
    processed/faiss_index/index.pkl
"""
import os
import sys
import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Allow imports from parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_config import PROCESSED_DIR, PREFERRED_DATASETS, FAISS_INDEX_DIR, EMBEDDING_MODEL, LLM_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _summarize_dataset_row(rec: dict, asset_id: str, dataset: str) -> str:
    """
    Convert a structural asset statistics dictionary into a natural-language string
    suitable for embedding and semantic retrieval.
    """
    parts = [f"Infrastructure Asset: {asset_id}", f"Source Dataset: {dataset}"]

    if rec.get("mean_risk") is not None:
        risk_label = "CRITICAL" if rec["max_risk"] >= 0.75 else ("HIGH" if rec["max_risk"] >= 0.50 else "LOW")
        parts.append(f"Predicted Risk Score: mean={rec['mean_risk']:.4f}, peak={rec['max_risk']:.4f} [{risk_label}]")

    if rec.get("mean_anomaly") is not None:
        anomaly_label = "ABNORMAL" if rec["max_anomaly"] >= 0.70 else "NORMAL"
        parts.append(f"Autoencoder Anomaly Score: mean={rec['mean_anomaly']:.4f}, peak={rec['max_anomaly']:.4f} [{anomaly_label}]")

    if rec.get("alert_count"):
        parts.append(f"Anomaly Alert Events: {rec['alert_count']} flag(s) triggered")

    if rec.get("mean_shift") is not None:
        shift_label = "SIGNIFICANT DRIFT" if rec["mean_shift"] >= 0.60 else "stable"
        parts.append(f"Behavioral Shift Index: {rec['mean_shift']:.4f} [{shift_label}]")

    if rec.get("mean_dynamics") is not None:
        parts.append(f"Structural Dynamics Score: {rec['mean_dynamics']:.4f}")

    if rec.get("modal_state") is not None:
        modal_desc = {0: "Normal Baseline", 1: "Intermediate/Active Load", 2: "Altered Dynamics"}
        parts.append(f"Dominant Behavioral Mode: State {rec['modal_state']} ({modal_desc.get(rec['modal_state'], 'Unknown')})")

    if rec.get("readings"):
        parts.append(f"Total Sensor Readings: {rec['readings']}")

    return " | ".join(parts)


def build_structural_summaries() -> list[str]:
    """
    Reads all processed *_behavior.parquet files and generates
    natural-language structural summaries for embedding.
    """
    summaries = []

    for fname in PREFERRED_DATASETS:
        fpath = PROCESSED_DIR / fname
        if not fpath.exists():
            logger.warning(f"Dataset not found: {fname}")
            continue

        logger.info(f"Processing: {fname}")
        try:
            df = pd.read_parquet(fpath)
        except Exception as e:
            logger.error(f"Failed to load {fname}: {e}")
            continue

        id_col       = next((c for c in ['bridge_id', 'Bridge_ID', 'sensor_id', 'test_id'] if c in df.columns), None)
        anomaly_col  = next((c for c in df.columns if 'Autoencoder_Anomaly_Score' in c), None)
        alert_col    = next((c for c in df.columns if 'Anomaly_Alert_Flag' in c), None)
        risk_col     = next((c for c in df.columns if 'Predicted_Risk_Score' in c), None)
        shift_col    = next((c for c in df.columns if 'Behavioral_Shift_Index' in c), None)
        dynamics_col = next((c for c in df.columns if 'Structural_Dynamics_Score' in c), None)
        cluster_col  = next((c for c in df.columns if 'Behavioral_State_Cluster' in c), None)

        groups = [(fname.replace(".parquet",""), df)] if not id_col else \
                 [(str(aid), grp) for aid, grp in df.groupby(id_col)]

        for asset_id, grp in groups:
            rec = {
                "readings":      len(grp),
                "mean_anomaly":  grp[anomaly_col].mean()    if anomaly_col    else None,
                "max_anomaly":   grp[anomaly_col].max()     if anomaly_col    else None,
                "alert_count":   int(grp[alert_col].sum())  if alert_col      else 0,
                "mean_risk":     grp[risk_col].mean()       if risk_col       else None,
                "max_risk":      grp[risk_col].max()        if risk_col       else None,
                "mean_shift":    grp[shift_col].mean()      if shift_col      else None,
                "mean_dynamics": grp[dynamics_col].mean()   if dynamics_col   else None,
                "modal_state":   int(grp[cluster_col].mode()[0]) if cluster_col else None,
            }
            summary_str = _summarize_dataset_row(rec, asset_id, fname.replace(".parquet",""))
            summaries.append(summary_str)
            logger.info(f"  → {asset_id}: {summary_str[:80]}...")

    logger.info(f"Generated {len(summaries)} structural summaries for embedding.")
    return summaries


def build_vectorstore():
    """Main function: Generate summaries → embed → save FAISS index."""
    logger.info("Starting FAISS Vector Store Build...")

    summaries = build_structural_summaries()
    if not summaries:
        logger.error("No structural summaries generated. Cannot build vector store.")
        return

    logger.info(f"Embedding {len(summaries)} summaries using model: {EMBEDDING_MODEL}")

    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Install: pip install langchain-community faiss-cpu")
        return

    # Wrap summaries as LangChain Documents
    documents = [
        Document(page_content=s, metadata={"index": i, "summary": s[:100]})
        for i, s in enumerate(summaries)
    ]

    try:
        embeddings = OllamaEmbeddings(
            model=EMBEDDING_MODEL,
            base_url=LLM_BASE_URL
        )
        # Build FAISS index
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save to disk
        FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(FAISS_INDEX_DIR))
        logger.info(f"FAISS index saved to: {FAISS_INDEX_DIR}")
        logger.info("Vector store build complete.")

    except Exception as e:
        logger.error(f"Failed to build FAISS index: {e}")
        logger.error("Ensure Ollama is running and 'nomic-embed-text' model is pulled.")
        logger.info("Fallback: The agent will function with direct tool calls (no vector retrieval).")


if __name__ == "__main__":
    build_vectorstore()
