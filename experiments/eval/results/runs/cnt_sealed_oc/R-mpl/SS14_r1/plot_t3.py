import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Find the exact column name for 가동시간
col_time_candidates = [c for c in df_runs.columns if "가동시간" in str(c)]
if not col_time_candidates:
    raise ValueError("Column containing '가동시간' not found")
col_time_name = col_time_candidates[0]

# Convert the time column to numeric to ensure correct plotting and mean calculation
df_runs[col_time_name] = pd.to_numeric(df_runs[col_time_name], errors='coerce')

# Filter for R1 and R4 only
df_filtered = df_runs[df_runs['반응기'].isin(['R1', 'R4'])].copy()

# Calculate mean 가동시간 per reactor and week
grouped_mean = df_filtered.groupby(['반응기', '주차'])[col_time_name].mean().reset_index()

# Plotting
fig, ax = plt.subplots(figsize=(12, 6))

# Define colors for R1 and R4
colors = {'R1': '#1f77b4', 'R4': '#d62728'}
markers = {'R1': 'o', 'R4': 's'}

for reactor in ['R1', 'R4']:
    subset = grouped_mean[grouped_mean['반응기'] == reactor]
    # Sort by 주차 to ensure lines connect correctly
    subset = subset.sort_values('주차')
    
    ax.plot(subset['주차'], subset[col_time_name], 
            label=reactor, 
            color=colors[reactor], 
            marker=markers[reactor], 
            linewidth=2, 
            markersize=6)

# Set ticks and labels
weeks_to_include = list(range(1, 27))
ax.set_xticks(weeks_to_include)
ax.set_xlabel('주차')
ax.set_ylabel('평균 가동시간 (h)')
ax.set_title('R1 및 R4 반응기의 주간별 평균 가동시간 추이')
ax.legend(title='반응기')
ax.grid(True, linestyle='--', alpha=0.7)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "line_plot_r1_r4_mean_time.png")
plt.savefig(output_path, dpi=300)
plt.close()
