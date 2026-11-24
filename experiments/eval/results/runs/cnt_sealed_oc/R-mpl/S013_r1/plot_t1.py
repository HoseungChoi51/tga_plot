import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# The error suggests the '일자' column contains the literal string "yyyy-mm-dd" 
# or mixed formats that pandas can't auto-detect safely. 
# We will force parse with errors='coerce' to handle invalid rows, then drop them for calculation.
# However, looking at the preview, it says [날짜 2026-03-02~...], so most are valid.
# If the header itself is in row 1 and data starts row 2, sometimes read_excel picks up headers wrong.
# Let's ensure we treat '일자' correctly. If the column name is actually '일자', but values are weird:

# Try parsing directly with format specification if needed, but coerce first to be safe against one-off bad rows
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# Drop rows where date parsing failed (e.g., if "yyyy-mm-dd" was a stray value)
df = df.dropna(subset=['일자'])

# Extract Month
df['월'] = df['일자'].dt.month

# Define pass criteria: Grade A or B is considered passed (합격), C is fail (불합격)
df['합격여부'] = df['등급'].isin(['A', 'B']).astype(int)

# Pivot table for Heatmap
# Index: 반응기 (R1-R4)
# Columns: 월 (Month)
# Values: Mean of 합격여부 (which represents pass rate)
heatmap_data = df.pivot_table(index='반응기', columns='월', values='합격여부', aggfunc='mean')

# Ensure all months present in data are sorted
heatmap_data = heatmap_data.sort_index(axis=0).sort_index(axis=1)

# Create Plot
fig, ax = plt.subplots(figsize=(10, 6))

# Draw Heatmap using imshow
im = ax.imshow(heatmap_data.values, cmap='YlGnBu', aspect='auto', vmin=0, vmax=1)

# Ticks and Labels
ax.set_xticks(np.arange(len(heatmap_data.columns)))
ax.set_yticks(np.arange(len(heatmap_data.index)))
ax.set_xticklabels([f"{m}월" for m in heatmap_data.columns])
ax.set_yticklabels(heatmap_data.index)

# Rotate x labels slightly if needed
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("합격률", rotation=-90, va="bottom")

# Show numeric values on heatmap cells
for i in range(len(heatmap_data.index)):
    for j in range(len(heatmap_data.columns)):
        val = heatmap_data.iloc[i, j]
        if not np.isnan(val):
            # Format as percentage with 1 decimal place
            text = f"{val*100:.1f}"
            # Choose text color based on background brightness
            norm_val = im.norm(val)
            color = "white" if norm_val > 0.5 else "black"
            
            ax.text(j, i, text,
                    ha="center", va="center", color=color, fontsize=8)

# Titles
ax.set_title("반응기별 월간 합격률 (%) 히트맵")
ax.set_xlabel("월")
ax.set_ylabel("반응기")

# Tight layout
fig.tight_layout()

# Save
output_path = os.path.join(OUT_DIR, "reactor_monthly_pass_rate_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
