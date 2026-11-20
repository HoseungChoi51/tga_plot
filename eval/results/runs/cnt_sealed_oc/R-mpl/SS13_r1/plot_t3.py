import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 경로
file_path = "data/run_log.xlsx"

# 데이터 읽기 (시트 '런로그')
df = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름 매칭
col_x = None
for col in df.columns:
    if "체류시간" in str(col):
        col_x = col
        break

col_y = None
for col in df.columns:
    if "CNT수율" in str(col):
        col_y = col
        break
    elif "수율" in str(col) and "금속" not in str(col) and "생산" not in str(col):
        if col_y is None:
            col_y = col

col_lot = None
for col in df.columns:
    if "촉매로트" in str(col) or "로트" in str(col):
        col_lot = col
        break

if col_x is None or col_y is None or col_lot is None:
    raise ValueError(f"필요한 컬럼을 찾을 수 없습니다. x: {col_x}, y: {col_y}, lot: {col_lot}. Available columns: {list(df.columns)}")

print(f"Using X column: '{col_x}'")
print(f"Using Y column: '{col_y}'")
print(f"Using Lot column: '{col_lot}'")

# 데이터 전처리
plot_df = df[[col_x, col_y, col_lot]].copy()

# 결측치 처리 및 수치형 변환
plot_df[col_x] = pd.to_numeric(plot_df[col_x], errors='coerce')
plot_df[col_y] = pd.to_numeric(plot_df[col_y], errors='coerce')
plot_df = plot_df.dropna(subset=[col_x, col_y])

# 촉매 로트 그룹화: old vs new
# old = FC-2602 ~ FC-2605
# new = FC-2606 ~ FC-2608
def categorize_lot(lot):
    if pd.isna(lot):
        return "Unknown"
    lot_str = str(lot).strip()
    import re
    match = re.search(r'(\d+)', lot_str)
    if match:
        num = int(match.group(1))
        if 2602 <= num <= 2605:
            return "Old"
        elif 2606 <= num <= 2608:
            return "New"
    return "Other"

plot_df['Group'] = plot_df[col_lot].apply(categorize_lot)

# 그룹별 색상 정의
colors = {"Old": "#1f77b4", "New": "#ff7f0e"}

# Binning 설정
# Bin width 0.25s, range 2.5 - 6.75
bin_edges = np.linspace(2.5, 6.75, num=int((6.75-2.5)/0.25)+1)

# Apply binning
# right=False means intervals are [a, b)
plot_df['BinIndex'] = pd.cut(plot_df[col_x], bins=bin_edges, right=False, labels=False)

# Calculate midpoints for each bin index to use later
# We can create a mapping from BinIndex to Midpoint
midpoints = {}
for i in range(len(bin_edges) - 1):
    midpoints[i] = (bin_edges[i] + bin_edges[i+1]) / 2

# Group by Lot Group and BinIndex, calculate mean CNT yield and count
grouped = plot_df.groupby(['Group', 'BinIndex']).agg(
    MeanYield=(col_y, 'mean'),
    Count=(col_y, 'size')
).reset_index()

# Filter out bins with n < 10
filtered_grouped = grouped[grouped['Count'] >= 10]

# Prepare data for plotting
groups_to_plot = ["Old", "New"]

fig, ax = plt.subplots(figsize=(12, 8))

for group in groups_to_plot:
    subset = filtered_grouped[filtered_grouped['Group'] == group].copy()
    
    if not subset.empty:
        # Map BinIndex to Midpoint
        subset['Midpoint'] = subset['BinIndex'].map(midpoints)
        
        # Sort by midpoint to ensure lines connect correctly
        subset = subset.sort_values('Midpoint')
        
        ax.plot(subset['Midpoint'], subset['MeanYield'], 
                marker='o', 
                linestyle='-', 
                color=colors[group], 
                label=f"{group} Lots",
                linewidth=2,
                markersize=6)

# Labels and Title
ax.set_xlabel("체류시간 Bin Midpoint (s)", fontsize=12)
ax.set_ylabel("평균 CNT수율 (g/g-cat)", fontsize=12)
ax.set_title("Average CNT Yield per Residence Time Bin (n ≥ 10)", fontsize=14)

# Grid
ax.grid(True, linestyle="--", alpha=0.5)

# Legend
ax.legend(title="Catalyst Lot Group", loc="best")

# Save
output_file = os.path.join(OUT_DIR, "avg_yield_per_bin_by_lot_group.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
