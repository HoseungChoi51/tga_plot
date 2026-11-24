import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 가동시간 컬럼 찾기 및 숫자형으로 변환
col_runtime = None
for col in df.columns:
    if '가동시간' in str(col):
        col_runtime = col
        break

if col_runtime is None:
    # 폴백: 미리보기상 P는 16번째 열 (index 15)
    col_runtime = df.columns[15]

# 데이터를 추출하고 강제로 float 타입으로 변환하여 카테고리 처리 문제 방지
runtime_data = pd.to_numeric(df[col_runtime], errors='coerce').dropna()

# 히스토그램 플롯 설정
fig, ax = plt.subplots(figsize=(10, 6))

# bins: 2부터 17까지 1 간격 -> [2, 3, ..., 17] 경계선으로 총 15개 구간
bins = np.arange(2, 18, 1)

ax.hist(runtime_data, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)

# 라벨링 및 제목
ax.set_xlabel('가동시간 (h)', fontsize=12)
ax.set_ylabel('빈도 (수)', fontsize=12)
ax.set_title('CNT 생산 런별 가동시간 분포 (중간 종료 런 확인용)', fontsize=14)
ax.set_xticks(bins) # x축 눈금을 bin 경계에 맞춤
ax.grid(axis='y', linestyle='--', alpha=0.5)

# 저장
output_filename = os.path.join(OUT_DIR, "runtime_histogram.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
