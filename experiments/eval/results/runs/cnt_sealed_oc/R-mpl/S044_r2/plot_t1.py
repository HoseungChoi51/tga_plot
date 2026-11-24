import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 데이터 전처리
# 원인별 정지 횟수 계산 (반응기 x 원인)
pivot_counts = df.pivot_table(index='반응기', columns='원인', values='일자', aggfunc='count')

# 열 순서 정리 (알파벳/한글 순으로 정렬하여 일관성 유지)
pivot_counts = pivot_counts.reindex(sorted(pivot_counts.columns), axis=1)

# 결측값 0으로 채우기
pivot_counts = pivot_counts.fillna(0).astype(int)

# 플롯 그리기
fig, ax = plt.subplots(figsize=(12, 6))

# 표 형태로 보이게 하되, 색으로 차이를 두기 위해 imshow 또는 heatmap 스타일 사용
# 하지만 사용자가 "표처럼" 보여달라고 했으므로, matplotlib의 table 기능을 쓰거나
# seaborn style의 heatmap을 쓸 수 있음. 여기서는 pandas plot의 bar chart보다는
# 시각적 비교를 쉽게 하기 위해 Heatmap (imshow)을 사용하되, 숫자를 텍스트로 오버레이함.

im = ax.imshow(pivot_counts.values, cmap='YlOrRd', aspect='auto')

# 눈금 설정
ax.set_xticks(np.arange(len(pivot_counts.columns)))
ax.set_yticks(np.arange(len(pivot_counts.index)))
ax.set_xticklabels(pivot_counts.columns)
ax.set_yticklabels(pivot_counts.index)

# 축 라벨
ax.set_xlabel("정지 원인")
ax.set_ylabel("반응기")
ax.set_title("반응기별 정지 원인 빈도 분석 (색상: 정지 횟수)")

# 색상 바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("정지 횟수", rotation=-90, va="bottom")

# 각 셀에 숫자 표시
for i in range(len(pivot_counts.index)):
    for j in range(len(pivot_counts.columns)):
        text = ax.text(j, i, pivot_counts.iloc[i, j],
                       ha="center", va="center", color="black")

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "downtime_frequency_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
