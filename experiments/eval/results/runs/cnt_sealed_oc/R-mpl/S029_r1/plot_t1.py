import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# 데이터 전처리 및 그룹화
# 2존온도(C)와 H2/C2H4비(D)를 기준으로 순도(G)의 평균을 계산
pivot_table = df.pivot_table(index='2존온도(°C)', columns='H2/C2H4비', values='순도(%)', aggfunc='mean')

# 히트맵 그리기
fig, ax = plt.subplots(figsize=(10, 8))

im = ax.imshow(pivot_table.values, cmap='viridis', aspect='auto', origin='lower')

# 눈금 설정
ax.set_xticks(np.arange(len(pivot_table.columns)))
ax.set_yticks(np.arange(len(pivot_table.index)))
ax.set_xticklabels(pivot_table.columns)
ax.set_yticklabels(pivot_table.index)

# 레이블 추가
ax.set_xlabel('H2/C2H4비')
ax.set_ylabel('2존온도(°C)')
ax.set_title('DOE 결과: 2존온도 × H2/C2H4비 순도(%) 평균 히트맵')

# 색상바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('순도(%)', rotation=-90, va="bottom")

# 셀에 값 텍스트 표시
for i in range(len(pivot_table.index)):
    for j in range(len(pivot_table.columns)):
        text = ax.text(j, i, f"{pivot_table.iloc[i, j]:.2f}",
                       ha="center", va="center", color="w")

# 레이아웃 조정 및 저장
plt.tight_layout()
save_path = os.path.join(OUT_DIR, "doe_purity_heatmap.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
