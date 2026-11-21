import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# 그룹화: H2 비율과 온도에 따른 평균 수율 계산
# 피벗 테이블을 사용하여 각 H2 비율별 온도-수율 관계를 얻음
pivot_df = df.pivot_table(values='수율(g/g-cat)', index='2존온도(°C)', columns='H2/C2H4비', aggfunc='mean')

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

# 색상 팔레트 생성 (H2 비율 개수만큼 색상 할당)
h2_ratios = pivot_df.columns.values
colors = plt.cm.viridis(np.linspace(0, 1, len(h2_ratios)))

# 각 H2 비율에 대해 선 그래프 작성
for i, ratio in enumerate(h2_ratios):
    temps = pivot_df.index.values
    yields = pivot_df[ratio].values
    
    # 선 플롯
    ax.plot(temps, yields, marker='o', linestyle='-', color=colors[i], label=f'H2/C2H4 = {ratio}', linewidth=2, markersize=6)

# 축 라벨 및 제목
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('평균 수율 (g/g-cat)', fontsize=12)
ax.set_title('DOE 결과: H2 비율별 2존 온도에 따른 CNT 수율 변화', fontsize=14)
ax.legend(title='H2/C2H4 비율', loc='best')
ax.grid(axis='both', linestyle='--', alpha=0.5)

# X축 눈금 조정 (온도가 이산적이므로 해당 값만 표시)
ax.set_xticks(pivot_df.index.values)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "doe_yield_vs_temp_by_h2.png")
plt.savefig(save_path, dpi=300)
plt.close()
