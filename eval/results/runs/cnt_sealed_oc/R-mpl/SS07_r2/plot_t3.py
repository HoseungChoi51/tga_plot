import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t3"
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
r4_data = df_valid[df_valid[col_reactor] == 'R4'][col_metal].values
others_data = df_valid[df_valid[col_reactor].isin(['R1', 'R2', 'R3'])][col_metal].values

# 히스토그램 범위와 빈 설정
min_val = 1.75
max_val = 6.5
bin_width = 0.25
bins = np.arange(min_val, max_val + bin_width, bin_width)

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 겹쳐서 그리기 (반투명, density=True로 밀도 표시)
ax.hist(others_data, bins=bins, color='steelblue', edgecolor='black', alpha=0.5, label='R1-R3 (나머지)', density=True)
ax.hist(r4_data, bins=bins, color='orange', edgecolor='black', alpha=0.5, label='R4', density=True)

# 규격 상한선 추가 (5.0 wt%)
spec_limit = 5.0
ax.axvline(x=spec_limit, color='red', linestyle='--', linewidth=2, label=f'규격 상한 ({spec_limit} wt%)')

ax.set_xlabel('잔류금속 (wt%)')
ax.set_ylabel('밀도 (Density)')
ax.set_title('CNT 생산 런별 잔류금속 분포 히스토그램 (R4 vs 나머지, 밀도 기준)')

# x축 범위 제한
ax.set_xlim(min_val, max_val)

# y축 눈금 정수로 표시하지 않음 (밀도는 소수점이므로 기본값 사용 또는 MaxNLocator 조정 가능하지만 밀도 값이 작을 수 있으므로 자동 스케일 유지)
# ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True)) # 이 줄은 제거하거나 주석 처리해야 함 (밀도이기 때문)

# 레전드 추가
ax.legend(loc='upper right')

# 그리드 추가
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 저장
output_file = os.path.join(OUT_DIR, "histogram_metal_content_r4_vs_others_density.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
