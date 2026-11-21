import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
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
    # 번호 추출 시도 (예: FC-2603 -> 2603)
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
colors = {"Old": "#1f77b4", "New": "#ff7f0e", "Other": "gray", "Unknown": "lightgray"}

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 7))

groups_to_plot = ["Old", "New"]
for group in groups_to_plot:
    subset = plot_df[plot_df['Group'] == group]
    if not subset.empty:
        ax.scatter(subset[col_x], subset[col_y], 
                   label=group, 
                   color=colors[group], 
                   alpha=0.6, 
                   edgecolors='w', 
                   s=50)

# Other/Unknown이 있다면 회색으로 표시할 수도 있으나, 요청에 명시되지 않은 경우 생략하거나 범례에 포함
subset_other = plot_df[~plot_df['Group'].isin(groups_to_plot)]
if not subset_other.empty:
    ax.scatter(subset_other[col_x], subset_other[col_y], 
               label="Other", 
               color="gray", 
               alpha=0.3, 
               edgecolors='none', 
               s=30)

# 라벨 및 제목 설정
ax.set_xlabel(str(col_x), fontsize=12)
ax.set_ylabel(str(col_y), fontsize=12)
ax.set_title("Scatter Plot: 체류시간 vs CNT수율 (Color by Catalyst Lot Group)", fontsize=14)

# 격자 추가
ax.grid(True, linestyle="--", alpha=0.5)

# 범례 추가
ax.legend(title="Catalyst Lot Group", loc="best")

# 파일 저장
output_file = os.path.join(OUT_DIR, "scatter_residence_time_vs_yield_colored.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
