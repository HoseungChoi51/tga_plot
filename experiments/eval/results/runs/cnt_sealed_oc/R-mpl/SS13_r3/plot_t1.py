import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns containing the keywords to handle potential whitespace or encoding differences
col_residence = None
col_yield = None

for col in df.columns:
    if '체류시간' in str(col):
        col_residence = col
    if 'CNT수율' in str(col) or ('수율' in str(col) and 'g/g-cat' in str(col)):
        col_yield = col

if col_residence is None or col_yield is None:
    raise ValueError("Could not find required columns for residence time or yield.")

# Extract required columns and convert to numeric
# The error indicates that the data might be mixed with non-numeric values or read as objects/categories
x_data = pd.to_numeric(df[col_residence], errors='coerce')
y_data = pd.to_numeric(df[col_yield], errors='coerce')

# Drop rows where conversion failed (NaNs) to ensure clean plotting
mask = x_data.notna() & y_data.notna()
x_clean = x_data[mask]
y_clean = y_data[mask]

# Create plot
plt.figure(figsize=(10, 7))
plt.scatter(x_clean, y_clean, alpha=0.6, edgecolors='k', s=50, label='Runs')

# Add labels and title using the detected column names for accuracy
plt.xlabel(str(col_residence), fontsize=12)
plt.ylabel(str(col_yield), fontsize=12)
plt.title('Scatter Plot: 체류시간 vs CNT수율 (All Runs)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Save figure
output_file = os.path.join(OUT_DIR, 'scatter_residence_time_vs_yield.png')
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
