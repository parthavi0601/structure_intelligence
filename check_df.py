import pandas as pd
df = pd.read_parquet('processed/failure_prediction_behavior.parquet')
with open('df_out.txt', 'w', encoding='utf-8') as f:
    f.write(f"Columns: {list(df.columns)}\n")
    f.write(f"Autoencoder_Anomaly_Score in columns: {'Autoencoder_Anomaly_Score' in df.columns}\n")
    if 'Predicted_Risk_Score' in df.columns:
        f.write(f"Predicted_Risk_Score min: {df['Predicted_Risk_Score'].min()} max: {df['Predicted_Risk_Score'].max()}\n")
