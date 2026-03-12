import os
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROCESSED_DIR = "processed"

def analyze_structural_behavior(df, dataset_name):
    """
    Analyzes structural behavior by finding operational states
    and calculating a behavioral shift index.
    """
    logger.info(f"Analyzing behavioral dynamics for: {dataset_name}")
    
    # 1. Select relevant structural response features
    # Try to find vibration, frequency, strain, acceleration columns
    structural_cols = [c for c in df.columns if any(kw in c.lower() for kw in 
        ['accel', 'vibration', 'strain', 'rms', 'freq', 'peak', 'deflection', 'tilt'])]
    
    # If no specific structural cols found, use all numeric columns (fallback)
    if not structural_cols:
        logger.warning(f"No explicit structural cols found in {dataset_name}. Using all numeric columns.")
        structural_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
    # Remove metadata/target columns from behavioral features
    exclude = ['test_id', 'bridge_id', 'sensor_id', 'damage_class', 'maintenance_flag', 'timestamp', 'time_start_s']
    structural_cols = [c for c in structural_cols if c not in exclude]
    
    if len(structural_cols) == 0:
        logger.warning(f"No numeric columns available in {dataset_name} for behavioral analysis. Skipping.")
        return df

    X = df[structural_cols].fillna(0)
    
    # 2. Operational Modal Behavior Tracking (Clustering States)
    # Using Gaussian Mixture Models to find probabilistic behavioral states
    # Assuming 3 states: Normal, Intermediate, Altered
    logger.info(f"Fitting GMM on {len(structural_cols)} structural features to identify Behavioral States...")
    gmm = GaussianMixture(n_components=3, random_state=42, covariance_type='diag')
    behavior_states = gmm.fit_predict(X)
    df['Behavioral_State_Cluster'] = behavior_states
    
    # Calculate log-likelihood of each sample under the GMM (lower implies deviation from norm)
    # We invert it so higher score = higher shift/abnormality in behavior
    log_probs = gmm.score_samples(X)
    df['Behavioral_Shift_Index'] = -log_probs
    
    # Normalize the behavioral shift index to [0.0, 1.0] for easier consumption by the Anomaly Detection module
    min_val = df['Behavioral_Shift_Index'].min()
    max_val = df['Behavioral_Shift_Index'].max()
    if max_val > min_val:
        df['Behavioral_Shift_Index'] = (df['Behavioral_Shift_Index'] - min_val) / (max_val - min_val)
    else:
        df['Behavioral_Shift_Index'] = 0.0

    # 3. Structural Dynamics Isolation (Isolation Forest)
    # Isolates regions of phase space where structural vibration/strain behaves randomly or out-of-distribution
    logger.info("Fitting Isolation Forest for structural dynamics deviation...")
    iso = IsolationForest(contamination=0.05, random_state=42)
    iso.fit(X)
    # decision_function gives positive scores for normal, negative for abnormal.
    # Invert and normalize to 0-1 range where 1 is highly abnormal behavior
    iso_scores = iso.decision_function(X)
    df['Structural_Dynamics_Score'] = -iso_scores
    
    min_iso = df['Structural_Dynamics_Score'].min()
    max_iso = df['Structural_Dynamics_Score'].max()
    if max_iso > min_iso:
        df['Structural_Dynamics_Score'] = (df['Structural_Dynamics_Score'] - min_iso) / (max_iso - min_iso)
    else:
        df['Structural_Dynamics_Score'] = 0.0

    return df

def run_behavioral_analysis():
    if not os.path.exists(PROCESSED_DIR):
        logger.error(f"Directory {PROCESSED_DIR} not found.")
        return
        
    parquet_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.parquet')]
    
    if not parquet_files:
        logger.error(f"No parquet files found in {PROCESSED_DIR}.")
        return

    # To satisfy "use the output from this feature to the next feature",
    # we save the analyzed parquets over the existing ones OR as a new file so the anomaly detection can pick it up.
    # Saving as *_behavior.parquet to keep pipeline clean. Next stage can load these.
    
    for file in parquet_files:
        # Ignore already processed behavior files if script is run multiple times
        if '_behavior.parquet' in file:
            continue
            
        filepath = os.path.join(PROCESSED_DIR, file)
        logger.info(f"Loading {filepath}...")
        try:
            df = pd.read_parquet(filepath)
            
            # Run the behavioral analysis
            df_analyzed = analyze_structural_behavior(df, file)
            
            # Save the new dataframe
            out_filename = file.replace('.parquet', '_behavior.parquet')
            out_filepath = os.path.join(PROCESSED_DIR, out_filename)
            df_analyzed.to_parquet(out_filepath, index=False)
            logger.info(f"Saved behavioral characteristics to {out_filepath}")
            logger.info("-" * 40)
        except Exception as e:
            logger.error(f"Failed to process {file}: {e}")

if __name__ == "__main__":
    logger.info("Starting Structural Behavior Analysis Pipeline...")
    run_behavioral_analysis()
    logger.info("Structural Behavior Analysis Completed Successfully.")
