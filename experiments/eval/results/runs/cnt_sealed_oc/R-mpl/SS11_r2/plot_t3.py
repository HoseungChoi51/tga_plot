import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# 피벗 테이블 생성: 인덱스=온도, 컬럼=H2비율, 값=수율 평균
pivot_df = df.pivot_table(values='수율(g/g-cat)', index='2존온도(°C)', columns='H2/C2H4비', aggfunc='mean')

# 히트맵 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# imshow 사용 시 원본 행 순서가 뒤집혀 보일 수 있으므로, 온도 순서를 유지하기 위해 
# pivot_df의 인덱스를 정렬하거나 extent를 조정할 수 있음. 
# 여기서는 자연스러운 증가 방향을 위해 origin='lower' 또는 y축 반전 처리가 필요할 수 있으나,
# 일반적인 히트맵은 위쪽이 높은 값을 의미하는 경우가 많으므로 그대로 두고 
# y축 라벨을 명확히 하는 것이 좋습니다. (matplotlib heatmap default is top-left origin)

im = ax.imshow(pivot_df.values, cmap='YlGnBu', aspect='auto', interpolation='nearest')

# 눈금 설정
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels([f"{c}" for c in pivot_df.columns])
ax.set_yticklabels([f"{t:.0f}" for t in pivot_df.index])

# 축 라벨
ax.set_xlabel('H2/C2H4 비율', fontsize=12)
ax.set_ylabel('2존 온도 (°C)', fontsize=12)
ax.set_title('DOE 결과: 온도 및 H2 비율에 따른 CNT 수율 분포 (히트맵)', fontsize=14)

# 셀 안에 값 표시
for i in range(len(pivot_df.index)):
    for j in range(len(pivot_df.columns)):
        val = pivot_df.iloc[i, j]
        # 배경색과 대비되는 글자색 선택 (단순화: 어두운 색이면 흰색, 밝은 색이면 검은색)
        text_color = "white" if im.norm(val) < 0.5 else "black"
        ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=text_color, fontsize=9)

# 컬러바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 수율 (g/g-cat)', rotation=-90, va="bottom", fontsize=10)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "doe_yield_heatmap.png")
plt.savefig(save_path, dpi=300)
plt.close()
