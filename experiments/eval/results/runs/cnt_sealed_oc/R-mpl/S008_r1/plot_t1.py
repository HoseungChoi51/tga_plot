import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set output directory and font
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the data file
file_path = "data/run_log.xlsx"

# Load sheet '런로그'
df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Clean column names to remove potential leading/trailing spaces or hidden characters
df_runs.columns = df_runs.columns.str.strip()

# Identify the yield column based on the error message provided in previous turn
# The available columns were: ['런ID', '일자', '주차', ..., 'CNT수율', ...]
yield_col = 'CNT수율'

if yield_col not in df_runs.columns:
    raise ValueError(f"Column '{yield_col}' not found. Available: {list(df_runs.columns)}")

# Ensure '주차' is numeric for sorting
df_runs['주차'] = pd.to_numeric(df_runs['주차'], errors='coerce')

# Calculate mean yield per week using the identified column
weekly_stats = df_runs.groupby('주차')[yield_col].mean().reset_index()
weekly_stats.columns = ['Week', 'Mean_Yield']

# Sort by week and drop NaNs
weekly_stats = weekly_stats.dropna(subset=['Week'])
weekly_stats['Week'] = weekly_stats['Week'].astype(int)
weekly_stats = weekly_stats.sort_values('Week')

# Create the plot
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(weekly_stats['Week'], weekly_stats['Mean_Yield'], marker='o', linestyle='-', color='#1f77b4', label='주별 평균 CNT 수율')

# Add vertical dotted line at Week 14
target_week = 14

ax.axvline(x=target_week, color='red', linestyle=':', linewidth=1.5, alpha=0.8)

# Add annotation text
# Determine Y position for text
y_min = weekly_stats['Mean_Yield'].min()
y_max = weekly_stats['Mean_Yield'].max()
text_y_pos = y_min + (y_max - y_min) * 0.85

ax.text(target_week + 0.3, text_y_pos, 'FC-2606 투입', rotation=90, va='center', ha='left', fontsize=10, color='red')

# Labels and Title
ax.set_xlabel('주차 (Week)', fontsize=12)
ax.set_ylabel('평균 CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('반응기 구분 없는 전체 주차별 평균 CNT 수율 추이', fontsize=14)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(loc='best')

# Adjust layout
plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "weekly_yield_trend.png")
plt.savefig(output_file, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_file}")
