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
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# 피벗 테이블 생성: 반응기별(Col), 원인별(Row) 정지 횟수(count) 계산
pivot_counts = df.pivot_table(index='원인', columns='반응기', values='일자', aggfunc='count')

# 원인의 순서를 알기 쉽게 정렬할 수 있으나, 요청에 명시되지 않았으므로 인덱스 기본값 사용
# 열(반응기)의 순서도 정렬 (R1~R4)
pivot_counts = pivot_counts.reindex(columns=['R1', 'R2', 'R3', 'R4'])

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 히트맵처럼 보이게 하되, 표 형식으로 수치 표시
im = ax.imshow(pivot_counts.values, cmap='YlOrRd', aspect='auto')

# 눈금 라벨 설정
ax.set_xticks(np.arange(len(pivot_counts.columns)))
ax.set_yticks(np.arange(len(pivot_counts.index)))
ax.set_xticklabels(pivot_counts.columns)
ax.set_yticklabels(pivot_counts.index)

# 셀 안에 숫자 표시
for i in range(len(pivot_counts.index)):
    for j in range(len(pivot_counts.columns)):
        text = ax.text(j, i, int(pivot_counts.values[i, j]),
                       ha="center", va="center", color="black")

# 축 레이블 및 제목
ax.set_xlabel("반응기")
ax.set_ylabel("정지 원인")
ax.set_title("반응기별 정지 원인별 발생 횟수")

# 색상 막대 추가 (선택 사항이지만 시각적 도움)
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("정지 횟수", rotation=-90, va="bottom")

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "downtime_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
