import os
import pandas as pd
import numpy as np
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROCESSED_DIR = "processed"

def predict_failure_risk(df, dataset_name):
    """
    Trains a Random Forest Regressor to predict infrastructure failure risk.
    """
    logger.info(f"Predicting failure risk for: {dataset_name}")
    
    # 1. Feature selection (use structural, environmental, and behavioral scores if available)
    feature_cols = [c for c in df.columns if any(kw in c.lower() for kw in 
        ['accel', 'vibration', 'strain', 'rms', 'freq', 'peak', 'deflection', 'tilt', 'temp', 'humidity', 'wind'])]
    
    # Add behavioral/anomaly scores as features if they exist
    additional_features = ['Behavioral_Shift_Index', 'Structural_Dynamics_Score', 'Autoencoder_Anomaly_Score']
    feature_cols += [c for c in additional_features if c in df.columns]
    
    # Target column (simulated or actual)
    target_col = 'forecast_score_next_30d' # We use the existing score as a proxy to learn from, creating a generalized dynamic model
    
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Cannot train dynamic risk model. Simulating risk.")
        # Create a synthetic target based on dynamics, anomaly and anomalies
        synthetic_risk = np.zeros(len(df))
        if 'Autoencoder_Anomaly_Score' in df.columns:
            synthetic_risk += df['Autoencoder_Anomaly_Score'] * 0.5
        if 'Behavioral_Shift_Index' in df.columns:
            synthetic_risk += df['Behavioral_Shift_Index'] * 0.3
        if 'Structural_Dynamics_Score' in df.columns:
            synthetic_risk += df['Structural_Dynamics_Score'] * 0.2
            
        df['Predicted_Risk_Score'] = np.clip(synthetic_risk, 0, 1)
        return df

    # Exclude non-predictive columns
    exclude = ['test_id', 'bridge_id', 'sensor_id', 'damage_class', 'maintenance_flag', 'timestamp', 'time_start_s', target_col]
    feature_cols = [c for c in feature_cols if c not in exclude]
    
    if len(feature_cols) == 0:
        logger.warning("No numeric columns available for risk prediction. Skipping.")
        return df

    logger.info(f"Training Risk Prediction Model using {len(feature_cols)} features...")
    
    X = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0) # Assuming this exists from original dataset as our ground truth
    
    # 2. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. Train Model
    rf_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_scaled, y)
    
    # 4. Predict
    df['Predicted_Risk_Score'] = rf_model.predict(X_scaled)
    
    # Normalize if needed, but forecast_score is usually 0-1
    df['Predicted_Risk_Score'] = np.clip(df['Predicted_Risk_Score'], 0, 1)
    
    logger.info(f"Average Predicted Risk Score: {df['Predicted_Risk_Score'].mean():.4f}")
    
    return df

def run_risk_pipeline():
    if not os.path.exists(PROCESSED_DIR):
        logger.error(f"Directory {PROCESSED_DIR} not found.")
        return
        
    parquet_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.parquet')]
    
    # Focus on files that have already gone through behavior AND anomaly
    # If a file has _behavior, it's good to use. Both behavior and anomaly scripts overwrite/use _behavior
    behavior_files = [f for f in parquet_files if f.endswith('_behavior.parquet')]
    
    if not behavior_files:
        logger.warning(f"No '*_behavior.parquet' files found. Will run on all parquets.")
        behavior_files = parquet_files
        
    for file in behavior_files:
        filepath = os.path.join(PROCESSED_DIR, file)
        logger.info(f"Loading {filepath}...")
        try:
            df = pd.read_parquet(filepath)
            
            # Predict risk
            df_analyzed = predict_failure_risk(df, file)
            
            # Save back
            df_analyzed.to_parquet(filepath, index=False)
            logger.info(f"Saved risk predictions to {filepath}")
            logger.info("-" * 40)
        except Exception as e:
            logger.error(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    logger.info("Starting Infrastructure Risk Prediction Pipeline...")
    run_risk_pipeline()
    logger.info("Infrastructure Risk Prediction Completed Successfully.")
