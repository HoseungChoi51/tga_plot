import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set output directory and ensure it exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Configure matplotlib for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: strip whitespace to handle potential trailing spaces in headers
df.columns = df.columns.str.strip()

# The error indicates the column name '외기습도 (%)' was not found exactly.
# This is likely due to hidden whitespace or encoding differences.
# We will find the correct column by checking which one contains '외기습도'.

humidity_col = None
metal_col = None
date_col = None

for col in df.columns:
    if '외기습도' in str(col):
        humidity_col = col
    if '잔류금속' in str(col):
        metal_col = col
    if '일자' in str(col) or 'Date' in str(col):
        date_col = col

if humidity_col is None or metal_col is None or date_col is None:
    raise ValueError("Could not identify required columns (Humidity, Metal Residue, Date).")

# Convert '일자' to datetime, coercing errors to NaT
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# Drop rows where date parsing failed if any exist
df = df.dropna(subset=[date_col])

# Extract month
df['월'] = df[date_col].dt.month

# Filter for months 3-8
df_plot = df[df['월'].between(3, 8)].copy()

# Prepare plotting
fig, ax = plt.subplots(figsize=(10, 7))

# Define unique months and colors
months = sorted(df_plot['월'].unique())
colors = plt.cm.viridis(np.linspace(0, 1, len(months)))

for i, m in enumerate(months):
    subset = df_plot[df_plot['월'] == m]
    ax.scatter(
        subset[humidity_col], 
        subset[metal_col], 
        color=colors[i], 
        label=f'{m}월', 
        alpha=0.6, 
        edgecolors='w', 
        linewidth=0.5, 
        s=40
    )

ax.set_xlabel('외기습도 (%)', fontsize=12)
ax.set_ylabel('잔류금속 (wt%)', fontsize=12)
ax.set_title('외기습도 vs 잔류금속 산점도 (월별 색상)', fontsize=14)
ax.legend(title='캘린더 월', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "humidity_vs_residual_metal_scatter.png")
plt.savefig(save_path, dpi=300)
plt.close(fig)
