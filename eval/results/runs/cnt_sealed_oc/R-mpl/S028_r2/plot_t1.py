import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 산화개시온도 (°C) 컬럼명 확인 및 전처리
col_temp = "산화개시온도 (°C)"
if col_temp not in df.columns:
    # 혹시 공백 차이 등 때문에 못 찾으면 유사한 이름 검색
    col_temp = [c for c in df.columns if "산화개시" in c][0]

# 결측치 제거
df_plot = df.dropna(subset=[col_temp, "반응기"]).copy()

# 그룹 분리: R4와 나머지(R1, R2, R3)
df_r4 = df_plot[df_plot["반응기"] == "R4"][col_temp]
df_rest = df_plot[df_plot["반응기"].isin(["R1", "R2", "R3"])][col_temp]

# 히스토그램 그리기
fig, ax = plt.subplots(figsize=(10, 6))

bins = np.arange(535, 611, 5)  # 535부터 610까지, 5 간격 (마지막 엣지 포함을 위해 611까지)

ax.hist(df_rest, bins=bins, alpha=0.6, label='R1–R3', color='skyblue', edgecolor='black')
ax.hist(df_r4, bins=bins, alpha=0.6, label='R4', color='salmon', edgecolor='black')

# 라벨 및 제목 설정
ax.set_xlabel("산화개시온도 (°C)", fontsize=12)
ax.set_ylabel("빈도 (Count)", fontsize=12)
ax.set_title("반응기 그룹별 산화개시온도 분포 히스토그램", fontsize=14)
ax.legend(loc='upper right', fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# x축 범위 고정
ax.set_xlim(535, 610)

# 저장
save_path = os.path.join(OUT_DIR, "oxidation_onset_hist.png")
plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.close()
