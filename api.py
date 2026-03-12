from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import math

app = FastAPI()

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROCESSED_DIR = "processed"

def format_data(df):
    # Convert numerical columns replacing NaN/INF for JSON serialization
    df = df.replace([math.inf, -math.inf], None)
    df = df.where(pd.notnull(df), None)
    return df

@app.get("/api/bridges")
def get_bridges():
    """Returns a list of unique bridge IDs or test IDs available in the dataset."""
    try:
        df_failure = pd.read_parquet(os.path.join(PROCESSED_DIR, "failure_prediction_behavior.parquet"))
        bridges = df_failure["bridge_id"].unique().tolist()
        return {"bridges": bridges}
    except Exception as e:
        return {"error": str(e), "bridges": ["Default Bridge"]}

@app.get("/api/behavioral-metrics/{bridge_id}")
def get_behavioral_metrics(bridge_id: str):
    """Returns the time series metrics for a specific bridge for the dashboard."""
    try:
        # Load the failure prediction behavior dataset which contains multiple bridges
        df = pd.read_parquet(os.path.join(PROCESSED_DIR, "failure_prediction_behavior.parquet"))
        
        # Filter for the requested bridge
        if bridge_id and bridge_id != "Default Bridge":
            df = df[df['bridge_id'] == bridge_id]
            
        # Select important columns to send back
        cols = [
            'Behavioral_Shift_Index', 
            'Structural_Dynamics_Score', 
            'Behavioral_State_Cluster', 
            'degradation_score', 
            'forecast_score_next_30d',
            'Predicted_Risk_Score',
            'structural_condition',
            'Autoencoder_Anomaly_Score',
            'Anomaly_Alert_Flag'
        ]
        
        # Ensure columns exist
        available_cols = [c for c in cols if c in df.columns]
        
        # We need a time proxy. Since failure_prediction.parquet has hour_sin but maybe no raw time,
        # we will just send an index-based sequential timestamp array or use its inherent temporal order.
        df['time_step'] = range(len(df))
        available_cols.insert(0, 'time_step')
        
        df_subset = df[available_cols].copy()
        
        # Downsample to a max of 200 points for performance on frontend chart
        if len(df_subset) > 200:
            step = len(df_subset) // 200
            df_subset = df_subset.iloc[::step]
            
        # Format for JSON
        records = format_data(df_subset).to_dict(orient="records")
        print(f"Sending {len(records)} records for bridge {bridge_id}")
        return {"data": records}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": []}
