import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os

# Configure fonts for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# File path from preview
FILE_PATH = "data/run_log.xlsx"
SHEET_NAME = "런로그"

# Read data
try:
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
except Exception as e:
    raise ValueError(f"Failed to read file {FILE_PATH}: {e}")

# Clean column names just in case they have extra spaces
df.columns = df.columns.str.strip()

# Identify relevant columns based on preview description
col_week = '주차'
col_reactor = '반응기'
col_igid = 'IG/ID'

# Check if columns exist
if col_week not in df.columns or col_reactor not in df.columns or col_igid not in df.columns:
    raise ValueError("Required columns (주차, 반응기, IG/ID) not found in the dataset.")

# Convert types to ensure proper plotting and pivoting
df[col_week] = pd.to_numeric(df[col_week], errors='coerce')
df[col_reactor] = df[col_reactor].astype(str).str.strip()
df[col_igid] = pd.to_numeric(df[col_igid], errors='coerce')

# Drop rows with missing values in key fields
df_clean = df.dropna(subset=[col_week, col_reactor, col_igid])

# Create a pivot table: Rows=Reactor, Columns=Week, Values=Mean IG/ID
pivot_df = df_clean.pivot_table(
    index=col_reactor, 
    columns=col_week, 
    values=col_igid, 
    aggfunc=np.mean
)

# Ensure weeks are sorted numerically
pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

# Sort reactors alphabetically for consistent ordering
pivot_df = pivot_df.sort_index()

# Prepare figure using imshow instead of seaborn heatmap
fig, ax = plt.subplots(figsize=(14, 6))

# Get numeric matrix for imshow
data_matrix = pivot_df.values
mask = np.isnan(data_matrix)
data_matrix_masked = np.ma.masked_where(mask, data_matrix)

# Plot heatmap-like image
im = ax.imshow(data_matrix_masked, cmap="viridis", aspect='auto', interpolation='nearest')

# Set ticks and labels
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels([f"{w:.0f}" for w in pivot_df.columns])
ax.set_yticklabels(pivot_df.index)

# Add colorbar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('평균 I_G/I_D', fontsize=12)

# Set titles and labels
ax.set_title("반응기별 주간 평균 I_G/I_D 변화 (Heatmap)", fontsize=16, pad=15)
ax.set_xlabel("주차 (Week)", fontsize=12)
ax.set_ylabel("반응기 (Reactor)", fontsize=12)

# Rotate x-axis labels if needed for readability
plt.xticks(rotation=45, ha='right')

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "reactor_weekly_igid_heatmap.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_path}")

# Close plot to free memory
plt.close()
