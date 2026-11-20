import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to handle potential whitespace issues
df.columns = df.columns.str.strip()

# Ensure '주차' is numeric and sort by it
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
df = df.dropna(subset=['주차'])
df = df.sort_values('주차')

# Identify the correct column name for CNT yield
# Based on preview: Q CNT수율 (g/g-cat)
yield_col = None
for col in df.columns:
    if 'CNT수율' in col or 'CNT Yield' in col:
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT yield column")

# Calculate weekly mean CNT yield (all reactors pooled)
weekly_mean_yield = df.groupby('주차')[yield_col].mean().reset_index()
weekly_mean_yield.columns = ['주차', '평균수율']

# Calculate 4-week trailing rolling mean
weekly_mean_yield['4주이동평균'] = weekly_mean_yield['평균수율'].rolling(window=4, min_periods=1).mean()

# Plotting
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(weekly_mean_yield['주차'], weekly_mean_yield['평균수율'], marker='o', linestyle='-', label='주간 평균 수율', color='blue')
ax.plot(weekly_mean_yield['주차'], weekly_mean_yield['4주이동평균'], marker='s', linestyle='--', label='4주 이동 평균', color='red', linewidth=2)

# Labels and Title
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('주차별 평균 CNT 수율 및 4주 이동 평균', fontsize=14)
ax.legend(loc='best', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.6)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "weekly_yield_rolling.png")
plt.savefig(output_path, dpi=300)
plt.close()
