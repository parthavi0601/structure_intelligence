"""
agent_config.py
===============
Central configuration for the Agentic AI Engineering Assistant.
Adjust the LLM_MODEL and thresholds here without touching other files.
"""
import os
from pathlib import Path

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).resolve().parent          # structure_intelligence/
PROCESSED_DIR = ROOT_DIR / "processed"
FAISS_INDEX_DIR = PROCESSED_DIR / "faiss_index"

# ─── LLM SETTINGS (Ollama) ────────────────────────────────────────────────────
# Preferred models: "llama3", "mistral", "gemma"
# Make sure `ollama pull llama3` has been run before starting the agent.
LLM_MODEL       = "llama3"
LLM_BASE_URL    = "http://localhost:11434"
LLM_TEMPERATURE = 0.1          # Low temperature → deterministic, factual answers

# Embedding model for FAISS vector store
EMBEDDING_MODEL = "nomic-embed-text"   # pull with: ollama pull nomic-embed-text

# ─── RISK THRESHOLDS ────────────────────────────────────────────────────────
CRITICAL_RISK   = 0.75   # Predicted_Risk_Score >= 0.75 → Immediate Inspection
HIGH_RISK       = 0.50   # Predicted_Risk_Score >= 0.50 → Elevated Priority
HIGH_ANOMALY    = 0.70   # Autoencoder_Anomaly_Score >= 0.70 → Significant anomaly
HIGH_SHIFT      = 0.60   # Behavioral_Shift_Index >= 0.60 → Significant drift

# ─── DATASET FILE NAMES ──────────────────────────────────────────────────────
# The agent prefers the enriched *_behavior.parquet files
PREFERRED_DATASETS = [
    "failure_prediction_behavior.parquet",
    "sensor_fusion_behavior.parquet",
    "behaviour_behavior.parquet",
    "digital_twin_behavior.parquet",
]

# ─── AGENT SETTINGS ───────────────────────────────────────────────────────────
AGENT_MAX_ITERATIONS = 6    # Max reasoning steps per query
VERBOSE_AGENT        = True  # Print LangChain reasoning steps to console
