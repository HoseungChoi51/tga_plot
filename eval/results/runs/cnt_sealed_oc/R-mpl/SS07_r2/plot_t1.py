import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# 데이터 읽기
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 필요 컬럼 추출 및 정제
col_name = '잔류금속 (wt%)'
if col_name not in df.columns:
    candidates = [c for c in df.columns if '잔류금속' in str(c)]
    if candidates:
        col_name = candidates[0]
    else:
        raise ValueError("Column '잔류금속 (wt%)' not found")

# 수치형으로 강제 변환 (문자열이나 다른 타입이 섞여 있을 경우를 대비)
metal_content = pd.to_numeric(df[col_name], errors='coerce').dropna()

# 히스토그램 범위와 빈 설정
min_val = 1.75
max_val = 6.5
bin_width = 0.25
bins = np.arange(min_val, max_val + bin_width, bin_width)

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 히스토그램绘制. 
# 주의: 이전 오류는 데이터에 NaN이나 문자열이 섞여 matplotlib가 category axis로 처리하려고 할 때 발생했습니다.
# pd.to_numeric(errors='coerce')를 사용하여 숫자가 아닌 값은 NaN으로 만들고 dropna로 제거하여 순수 float array로 전달합니다.
counts, bins_out, patches = ax.hist(metal_content.values, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)

ax.set_xlabel('잔류금속 (wt%)')
ax.set_ylabel('빈도수 (Count)')
ax.set_title('CNT 생산 런별 잔류금속 분포 히스토그램')

# x축 범위 제한
ax.set_xlim(min_val, max_val)

# y축 눈금 정수로 표시하기 위해 최대 count 확인 후 설정 (선택 사항이지만 깔끔함)
max_count = counts.max() if len(counts) > 0 else 0
if max_count > 0:
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# 그리드 추가
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 저장
output_file = os.path.join(OUT_DIR, "histogram_metal_content.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
