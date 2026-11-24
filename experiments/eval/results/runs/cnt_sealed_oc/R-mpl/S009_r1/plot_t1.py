import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the weekly summary sheet which contains the run count per week
file_path = "data/run_log.xlsx"
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# Extract relevant columns: 주차 (Week) and 런수 (Run Count)
weeks = df_weekly['주차']
run_counts = df_weekly['런수']

# Calculate the average number of runs over all 26 weeks
avg_run_count = run_counts.mean()

# Create the plot
fig, ax = plt.subplots(figsize=(12, 6))

# Plot bar chart for runs per week
bars = ax.bar(weeks, run_counts, color='steelblue', label='주차별 런 수')

# Add horizontal line for the average
ax.axhline(y=avg_run_count, color='red', linestyle='--', linewidth=2, label=f'평균 런 수 ({avg_run_count:.1f})')

# Customize labels and title
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('런 수', fontsize=12)
ax.set_title('주차별 CNT 생산 런 수 현황', fontsize=14)
ax.set_xticks(weeks) # Ensure all weeks are labeled if necessary, or let matplotlib decide
ax.legend(loc='upper right')

# Optional: Grid for better readability
ax.yaxis.grid(True, linestyle=':', alpha=0.7)
ax.set_axisbelow(True)

# Save the figure
output_path = os.path.join(OUT_DIR, "runs_per_week.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
