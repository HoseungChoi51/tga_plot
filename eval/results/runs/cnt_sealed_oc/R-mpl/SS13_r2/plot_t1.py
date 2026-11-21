import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# The previous error suggests that the column identified by '체류시간' might contain non-numeric data 
# (e.g., text headers mixed in or empty cells treated as objects/strings by pandas if the sheet structure is odd).
# However, looking at the preview, the data should be numeric.
# Let's robustly find the columns and ensure they are numeric before plotting.

col_x = None
col_y = None

for c in df.columns:
    if isinstance(c, str):
        # Check for residence time
        if '체류시간' in c:
            col_x = c
        # Check for CNT yield
        if 'CNT수율' in c:
            col_y = c

if col_x is None or col_y is None:
    raise ValueError(f"Could not find columns. Available: {df.columns.tolist()}")

# Convert to numeric, coercing errors to NaN to handle any stray text values
x_data = pd.to_numeric(df[col_x], errors='coerce')
y_data = pd.to_numeric(df[col_y], errors='coerce')

# Drop rows where either x or y is NaN after conversion
mask = ~(x_data.isna() | y_data.isna())
x_plot = x_data[mask]
y_plot = y_data[mask]

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(x_plot, y_plot, alpha=0.6, edgecolors='k', linewidths=0.5)

# Add labels and title using the actual column names found
plt.xlabel(col_x, fontsize=12)
plt.ylabel(col_y, fontsize=12)
plt.title('Scatter Plot: 체류시간 vs CNT수율 (All Runs)', fontsize=14)

# Save the plot
output_file = os.path.join(OUT_DIR, 'scatter_residence_time_vs_yield.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
