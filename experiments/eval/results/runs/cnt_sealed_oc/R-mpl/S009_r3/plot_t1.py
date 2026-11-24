import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# Calculate run count per week
# The '주차' column represents the week number (1~26)
run_counts_per_week = df_runs.groupby('주차').size().reset_index(name='런 수')

# Ensure the '주차' column is numeric for plotting to avoid dtype issues
run_counts_per_week['주차'] = pd.to_numeric(run_counts_per_week['주차'], errors='coerce')
run_counts_per_week = run_counts_per_week.dropna(subset=['주차'])
run_counts_per_week['주차'] = run_counts_per_week['주차'].astype(int)

# Sort by week to ensure correct order in plot
run_counts_per_week = run_counts_per_week.sort_values('주차')

# Calculate average run count across all 26 weeks
avg_run_count = run_counts_per_week['런 수'].mean()

# Plotting
fig, ax = plt.subplots(figsize=(12, 6))

# Use the integer x values directly
x_vals = run_counts_per_week['주차'].values
y_vals = run_counts_per_week['런 수'].values

bars = ax.bar(x_vals, y_vals, color='skyblue', edgecolor='black', label='주차별 런 수')

# Add horizontal line for the average
ax.axhline(y=avg_run_count, color='red', linestyle='--', linewidth=2, label=f'전체 평균 런 수: {avg_run_count:.2f}')

# Labels and Title
ax.set_xlabel('주차')
ax.set_ylabel('런 수')
ax.set_title('주차별 런 횟수 및 전체 평균')

# Ticks for x-axis to show all weeks clearly
ax.set_xticks(x_vals)
ax.set_xticklabels([str(w) for w in x_vals])

# Legend
ax.legend(loc='upper right')

# Grid
ax.yaxis.grid(True, linestyle=':', alpha=0.7)
ax.set_axisbelow(True)

# Save figure
output_file = os.path.join(OUT_DIR, "weekly_run_count.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
