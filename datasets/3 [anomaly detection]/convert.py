import scipy.io
import pandas as pd

# 1. Load the .mat file
mat_data = scipy.io.loadmat('SMC_Modal.m')

# 2. Identify the correct key
# .mat files often have 'header' keys we don't need (like __header__, __version__)
# We want the key that contains the actual sensor matrix.
keys = [k for k in mat_data.keys() if not k.startswith('_')]
print(f"Available data keys: {keys}")

# 3. Extract the data and convert to a DataFrame
# Replace 'vibration_matrix' with the actual key name found in step 2
data_key = keys[0] 
vibration_matrix = mat_data[data_key]

# 4. Create the DataFrame
df = pd.DataFrame(vibration_matrix)

# 5. Add column names (optional but helpful)
# Based on your previous dataset, you might have 5 or more sensors
df.columns = [f'Sensor_{i+1}' for i in range(df.shape[1])]

# 6. Export to CSV
df.to_csv('smc.csv', index=False)

print("Conversion complete: bridge_monitoring_data.csv")