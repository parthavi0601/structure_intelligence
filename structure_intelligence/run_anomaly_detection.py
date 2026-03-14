import os
import pandas as pd
import numpy as np
import logging
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROCESSED_DIR = "processed"

def detect_anomalies_autoencoder(df, dataset_name):
    """
    Trains an Autoencoder (MLP) on structural features.
    Computes reconstruction error as the anomaly score.
    """
    logger.info(f"Detecting structural anomalies for: {dataset_name}")
    
    # 1. Select relevant structural response features
    # Similar to behavior analysis, look for vibration, strain, displacement, etc.
    structural_cols = [c for c in df.columns if any(kw in c.lower() for kw in 
        ['accel', 'vibration', 'strain', 'rms', 'freq', 'peak', 'deflection', 'tilt', 'stress', 'displacement', 'temp'])]
    
    # Exclude metadata and previously engineered behavioral scores 
    # (though anomaly could use behavior scores, we will focus on raw/feature-engineered signals)
    exclude = ['test_id', 'bridge_id', 'sensor_id', 'damage_class', 'maintenance_flag', 'timestamp', 'time_start_s']
    exclude += ['Behavioral_State_Cluster', 'Behavioral_Shift_Index', 'Structural_Dynamics_Score']
    structural_cols = [c for c in structural_cols if c not in exclude]
    
    if len(structural_cols) == 0:
        logger.warning(f"No explicit structural cols found in {dataset_name}. Using all numeric columns.")
        structural_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        structural_cols = [c for c in structural_cols if c not in exclude]

    if len(structural_cols) == 0:
        logger.warning(f"No numeric columns available in {dataset_name} for anomaly detection. Skipping.")
        return df

    logger.info(f"Using {len(structural_cols)} features for Anomaly Detection (Autoencoder).")
    X = df[structural_cols].fillna(0)
    
    # 2. Scale features for Neural Network
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. Train Autoencoder
    # Using MLPRegressor to predict X_scaled from X_scaled
    # Bottleneck architecture: input -> 16 -> 8 -> 16 -> output
    logger.info("Training Autoencoder...")
    autoencoder = MLPRegressor(
        hidden_layer_sizes=(16, 8, 16),
        activation='relu',
        solver='adam',
        max_iter=50, # Keep it relatively low for speed, adjust if needed
        random_state=42,
        early_stopping=True
    )
    
    # Fit the model
    autoencoder.fit(X_scaled, X_scaled)
    
    # 4. Predict and calculate reconstruction error
    X_pred = autoencoder.predict(X_scaled)
    
    # Mean Squared Error per sample
    mse = np.mean(np.power(X_scaled - X_pred, 2), axis=1)
    
    # Normalize anomaly score from 0 to 1
    min_mse = mse.min()
    max_mse = mse.max()
    if max_mse > min_mse:
        normalized_score = (mse - min_mse) / (max_mse - min_mse)
    else:
        normalized_score = np.zeros_like(mse)
        
    df['Autoencoder_Anomaly_Score'] = normalized_score
    
    # 5. Threshold for Anomaly Alerts
    # E.g., top 5% of MSE are flagged as anomalies
    threshold = np.percentile(normalized_score, 95)
    df['Anomaly_Alert_Flag'] = (normalized_score > threshold).astype(int)
    
    logger.info(f"Identified {df['Anomaly_Alert_Flag'].sum()} anomalies based on 95th percentile threshold.")
    
    return df

def run_anomaly_pipeline():
    if not os.path.exists(PROCESSED_DIR):
        logger.error(f"Directory {PROCESSED_DIR} not found.")
        return
        
    parquet_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.parquet')]
    
    # Focus on files that have already gone through feature engineering or behavior analysis
    # E.g. _behavior.parquet files
    behavior_files = [f for f in parquet_files if f.endswith('_behavior.parquet')]
    
    if not behavior_files:
        logger.warning(f"No '*_behavior.parquet' files found. Will run on all parquets.")
        behavior_files = parquet_files
        
    if not behavior_files:
        logger.error("No parquet datasets available in processed_dir.")
        return

    for file in behavior_files:
        filepath = os.path.join(PROCESSED_DIR, file)
        logger.info(f"Loading {filepath}...")
        try:
            df = pd.read_parquet(filepath)
            
            # Sub-sample or batch if data is huge, but assuming fits in memory for this PoC
            df_analyzed = detect_anomalies_autoencoder(df, file)
            
            # Save back, replacing the existing behavior file to enrich the pipeline
            df_analyzed.to_parquet(filepath, index=False)
            logger.info(f"Saved anomaly scores to {filepath}")
            logger.info("-" * 40)
        except Exception as e:
            logger.error(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    logger.info("Starting Structural Anomaly Detection Pipeline...")
    run_anomaly_pipeline()
    logger.info("Structural Anomaly Detection Completed Successfully.")
