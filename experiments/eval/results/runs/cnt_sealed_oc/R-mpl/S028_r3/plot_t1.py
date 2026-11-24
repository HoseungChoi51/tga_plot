import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configure fonts for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Find the column that contains '산화개시온도' or similar keywords
target_col = None
for col in df.columns:
    if '산화개시' in str(col):
        target_col = col
        break

if target_col is None:
    raise ValueError("Could not find oxidation onset temperature column.")

# Prepare data: Filter valid rows and categorize reactors
# Drop NaNs for both columns to ensure clean plotting
df_valid = df.dropna(subset=[target_col, '반응기']).copy()

# Ensure the temperature column is numeric
df_valid[target_col] = pd.to_numeric(df_valid[target_col], errors='coerce')

# Drop any remaining NaNs after conversion
df_valid = df_valid.dropna(subset=[target_col])

# Create group labels: R4 vs Others (R1-R3)
# Use .copy() on the subset or assign directly if careful. 
# The previous error might have been due to mixed types or empty groups causing issues in some matplotlib versions, 
# but explicitly ensuring numeric dtype is the key fix here.
df_valid['Group'] = np.where(df_valid['반응기'].astype(str).str.strip() == 'R4', 'R4', 'R1-R3')

# Extract temperature data for plotting
temps_r4 = df_valid[df_valid['Group'] == 'R4'][target_col].values
temps_others = df_valid[df_valid['Group'] == 'R1-R3'][target_col].values

# Define bins: 5°C interval from 535 to 610
edges = np.arange(535, 611, 5) # Creates [535, 540, ..., 610]

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Histogram for R1-R3
ax.hist(temps_others, bins=edges, alpha=0.6, color='steelblue', label='R1-R3', edgecolor='black')

# Histogram for R4
ax.hist(temps_r4, bins=edges, alpha=0.6, color='coral', label='R4', edgecolor='black')

# Labels and Title
ax.set_xlabel('산화개시온도 (°C)')
ax.set_ylabel('빈도수 (Count)')
ax.set_title('산화개시온도 분포: R4 vs R1-R3')
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Set X-axis limits to match the request clearly
ax.set_xlim(530, 615)

# Save plot
output_filename = os.path.join(OUT_DIR, "oxidation_onset_hist_R4_vs_Others.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
