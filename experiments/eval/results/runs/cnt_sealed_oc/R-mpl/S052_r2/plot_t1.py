import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns by partial match to handle potential whitespace/formatting issues in headers
yield_col = None
metal_col = None

for c in df.columns:
    if 'CNT수율' in str(c):
        yield_col = c
    if '잔류금속' in str(c):
        metal_col = c

if yield_col is None or metal_col is None:
    raise ValueError(f"Could not find required columns. Available: {df.columns.tolist()}")

# Convert relevant numeric columns to float explicitly to fix TypeError: dtype->object
# The error indicates the columns contain strings (objects), likely due to formatting in Excel.
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')
df[metal_col] = pd.to_numeric(df[metal_col], errors='coerce')

# Also ensure grouping columns are strings just in case
df['촉매로트'] = df['촉매로트'].astype(str)
df['반응기'] = df['반응기'].astype(str)

# Drop rows where conversion failed (NaNs) to avoid issues with mean calculation
df_clean = df.dropna(subset=[yield_col, metal_col])

# Aggregate per (촉매로트, 반응기)
grouped = df_clean.groupby(["촉매로트", "반응기"]).agg({
    metal_col: "mean",
    yield_col: "mean"
}).reset_index()

# Check number of groups (should be 28)
print(f"Number of aggregated points: {len(grouped)}")

# Create plot
fig, ax = plt.subplots(figsize=(10, 8))

# Get unique catalyst lots for coloring and legend
lots = grouped["촉매로트"].unique()
colors = plt.cm.viridis(np.linspace(0, 1, len(lots)))

for idx, lot in enumerate(lots):
    subset = grouped[grouped["촉매로트"] == lot]
    ax.scatter(
        subset[metal_col],
        subset[yield_col],
        color=colors[idx],
        label=lot,
        s=100,
        alpha=0.7,
        edgecolors='w',
        linewidths=0.5
    )

ax.set_xlabel("평균 잔류금속 (wt%)", fontsize=12)
ax.set_ylabel("평균 CNT수율 (g/g-cat)", fontsize=12)
ax.set_title("촉매로트 및 반응기별 평균 성능 (잔류금속 vs 수율)", fontsize=14)
ax.legend(title="촉매로트", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "aggregated_lot_reactor.png")
plt.savefig(save_path, dpi=300)
plt.close()
