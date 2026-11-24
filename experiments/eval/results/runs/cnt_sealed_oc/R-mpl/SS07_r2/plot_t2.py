import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 필요 컬럼 추출 및 정제
col_metal = '잔류금속 (wt%)'
if col_metal not in df.columns:
    candidates = [c for c in df.columns if '잔류금속' in str(c)]
    if candidates:
        col_metal = candidates[0]
    else:
        raise ValueError("Column '잔류금속 (wt%)' not found")

col_reactor = '반응기'
if col_reactor not in df.columns:
    candidates = [c for c in df.columns if '반응기' in str(c)]
    if candidates:
        col_reactor = candidates[0]
    else:
        raise ValueError("Column '반응기' not found")

# 수치형으로 강제 변환 및 NaN 제거
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')
df_valid = df.dropna(subset=[col_metal])

# 그룹 분리
# R4 데이터
r4_data = df_valid[df_valid[col_reactor] == 'R4'][col_metal].values
# 나머지 (R1, R2, R3) 데이터
others_data = df_valid[df_valid[col_reactor].isin(['R1', 'R2', 'R3'])][col_metal].values

# 히스토그램 범위와 빈 설정
min_val = 1.75
max_val = 6.5
bin_width = 0.25
bins = np.arange(min_val, max_val + bin_width, bin_width)

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 겹쳐서 그리기 (반투명)
ax.hist(others_data, bins=bins, color='steelblue', edgecolor='black', alpha=0.5, label='R1-R3 (나머지)')
ax.hist(r4_data, bins=bins, color='orange', edgecolor='black', alpha=0.5, label='R4')

ax.set_xlabel('잔류금속 (wt%)')
ax.set_ylabel('빈도수 (Count)')
ax.set_title('CNT 생산 런별 잔류금속 분포 히스토그램 (R4 vs 나머지)')

# x축 범위 제한
ax.set_xlim(min_val, max_val)

# y축 눈금 정수로 표시
counts_others, _, _ = ax.hist(others_data, bins=bins) # 이미 그려졌지만 counts 확인용
counts_r4, _, _ = ax.hist(r4_data, bins=bins)
all_counts = np.concatenate((counts_others, counts_r4))
if len(all_counts) > 0:
    max_count = all_counts.max()
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# 레전드 추가
ax.legend(loc='upper right')

# 그리드 추가
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 저장
output_file = os.path.join(OUT_DIR, "histogram_metal_content_r4_vs_others.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
