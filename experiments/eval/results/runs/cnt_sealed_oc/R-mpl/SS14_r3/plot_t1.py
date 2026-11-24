import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# 데이터 전처리
# 주차는 1~26 범위, 반응기는 R1~R4
pivot_counts = df_runs.pivot_table(index='반응기', columns='주차', values='런ID', aggfunc='count')

# 열 순서 고정 (1~26)
all_weeks = list(range(1, 27))
pivot_counts = pivot_counts.reindex(columns=all_weeks, fill_value=0)

# 행 순서 고정 (R1~R4)
reactors = ['R1', 'R2', 'R3', 'R4']
pivot_counts = pivot_counts.reindex(index=reactors)

# Heatmap 그리기
fig, ax = plt.subplots(figsize=(12, 5))

# heatmap 데이터: numpy array로 변환
heatmap_data = pivot_counts.values

# imshow 사용
im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')

# 눈금 라벨 설정
ax.set_xticks(np.arange(len(all_weeks)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels(all_weeks)
ax.set_yticklabels(reactors)

# 셀마다 수치 표시
for i in range(len(reactors)):
    for j in range(len(all_weeks)):
        val = int(heatmap_data[i, j])
        text_color = 'black' if val < 10 else 'white'
        ax.text(j, i, str(val), ha='center', va='center', color=text_color, fontsize=8)

# 컬러바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('런 수', rotation=-90, va="bottom")

# 제목 및 라벨
ax.set_title('반응기별 주차별 런 수 Heatmap')
ax.set_xlabel('주차')
ax.set_ylabel('반응기')

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "heatmap_run_count.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
