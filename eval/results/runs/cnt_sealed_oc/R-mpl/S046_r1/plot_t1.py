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
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Identify the correct column name for CNT yield
# The preview shows 'Q CNT수율 (g/g-cat)' but sometimes spaces or encoding vary.
# We look for a column containing 'CNT' and '수율' to be robust.
yield_col = None
for col in df.columns:
    if 'CNT' in str(col) and '수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    # Fallback to exact match if fuzzy search fails, though it should have worked
    yield_col = 'CNT수율 (g/g-cat)'

# Ensure '주차' is numeric and sort by it just in case
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
df = df.dropna(subset=['주차', yield_col])
df = df.sort_values('주차')

# Calculate weekly mean CNT yield (pooled across all reactors)
weekly_mean_yield = df.groupby('주차')[yield_col].mean().reset_index()
weekly_mean_yield.columns = ['주차', 'Mean_Yield']

# Calculate 4-week trailing rolling mean
# Use min_periods=1 so the first few weeks have a value based on available data
weekly_mean_yield['Rolling_4W_Mean'] = weekly_mean_yield['Mean_Yield'].rolling(window=4, min_periods=1).mean()

# Plotting
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(weekly_mean_yield['주차'], weekly_mean_yield['Mean_Yield'], marker='o', linestyle='-', color='steelblue', label='주간 평균 CNT 수율')
ax.plot(weekly_mean_yield['주차'], weekly_mean_yield['Rolling_4W_Mean'], linestyle='--', color='red', linewidth=2, label='4주 이동평균')

ax.set_xlabel('주차')
ax.set_ylabel(f'CNT 수율 ({yield_col.split("(")[1].rstrip(")")})' if '(' in yield_col else 'CNT 수율')
ax.set_title('주차별 주간 평균 CNT 수율 및 4주 이동평균 (전체 반응기 합산)')
ax.legend(loc='best')
ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "weekly_yield_trend.png")
plt.savefig(save_path, dpi=300)
plt.close()
