import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify column names based on previous error logs (no units in headers)
# The runtime column is '가동시간'
runtime_col = '가동시간'
week_col = '주차'
reactor_col = '반응기'

# Check if columns exist
for col in [runtime_col, week_col, reactor_col]:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' not found.")

# Convert '주차' to numeric
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

# Filter for weeks 1-26 and drop invalid rows
df = df.dropna(subset=[week_col])
df = df[df[week_col].between(1, 26)]
df[week_col] = df[week_col].astype(int)

# Convert runtime to numeric and drop NaNs
df[runtime_col] = pd.to_numeric(df[runtime_col], errors='coerce')
df = df.dropna(subset=[runtime_col])

# Filter for only R1 and R4
df_filtered = df[df[reactor_col].isin(['R1', 'R4'])]

# Calculate mean 가동시간 per 주차 per 반응기
mean_data = df_filtered.groupby([week_col, reactor_col])[runtime_col].mean().reset_index()

# Pivot to make plotting easier (optional, but good for line plots with missing data handling)
# Or just plot by iterating groups
weeks = list(range(1, 27))

fig, ax = plt.subplots(figsize=(10, 6))

colors = {'R1': '#1f77b4', 'R4': '#ff7f0e'} # Standard blue and orange
markers = {'R1': 'o', 'R4': 's'}

for reactor in ['R1', 'R4']:
    # Extract data for this reactor
    sub_df = mean_data[mean_data[reactor_col] == reactor]
    
    # Align with full week range to handle missing weeks (though preview suggests complete coverage)
    # Create a series indexed by week, reindexed to 1-26, then interpolate or just skip? 
    # Line plots usually connect existing points. If a week is missing, it creates a gap or connects across.
    # Given the heatmap had zeros/missing, we should check if all weeks are present.
    
    week_series = sub_df.set_index(week_col)[runtime_col]
    week_series = week_series.reindex(weeks)
    
    # Plot
    ax.plot(weeks, week_series.values, 
            marker=markers[reactor], 
            linestyle='-', 
            color=colors[reactor], 
            label=f"{reactor} 평균 가동시간",
            linewidth=2)

ax.set_title("R1 및 R4 반응기 주간 평균 가동시간 추이")
ax.set_xlabel("주차")
ax.set_ylabel("평균 가동시간 (h)")
ax.legend(loc='best')
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xticks(weeks)
ax.set_xlim(1, 26)

plt.tight_layout()

output_path = os.path.join(OUT_DIR, "line_runtime_R1_R4.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Line plot saved to {output_path}")
