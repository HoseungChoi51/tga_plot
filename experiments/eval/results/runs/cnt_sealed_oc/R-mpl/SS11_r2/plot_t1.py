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
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# 데이터 전처리 및 그룹화
# 온도는 이산적인 값(1100~1200)이므로 카테고리 또는 수치형으로 취급 가능
# 요청: "온도에 따라 수율이 어떻게 달라지는지" -> 온도별 수율 분포/평균을 보여주는 것이 적절
# 박스플롯(Boxplot)은 분포와 이상치, 평균 경향을 한눈에 보여주기 좋음. 
# 하지만 반복 실험 데이터이므로, 각 온도에서의 평균 수율과 오차범위(error bar)를 포함한 막대그래프나
# 산점도+회귀선도 좋을 수 있음. DOE 특성상 요인 효과를 보는 것이 중요하므로,
# 온도별 평균 수율을 막대그래프로 나타내고, 개별 데이터 포인트를 점으로 오버레이하는 방식을 채택합니다.

# 온도별 통계 계산
grouped = df.groupby('2존온도(°C)')['수율(g/g-cat)']
mean_yields = grouped.mean()
std_yields = grouped.std()
counts = grouped.count()

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

x_vals = mean_yields.index.values
y_vals = mean_yields.values
err_vals = std_yields.values

# 막대그래프 (평균 수율)
bars = ax.bar(x_vals, y_vals, width=15, alpha=0.6, color='steelblue', label='평균 수율')

# 에러바 (표준편차)
ax.errorbar(x_vals, y_vals, yerr=err_vals, fmt='none', ecolor='black', capsize=5, linewidth=1.5)

# 개별 데이터 점 (오버레이)
for temp in x_vals:
    subset = df[df['2존온도(°C)'] == temp]['수율(g/g-cat)']
    # 점들을 약간 랜덤하게 퍼뜨려서 겹치는 것을 방지 (Jittering)
    jitter = np.random.normal(0, 3, size=len(subset))
    ax.scatter(temp + jitter, subset, color='darkred', s=20, zorder=3, edgecolors='white', linewidths=0.5)

# 축 라벨 및 제목
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('수율 (g/g-cat)', fontsize=12)
ax.set_title('DOE 결과: 2존 온도에 따른 CNT 수율 변화', fontsize=14)
ax.legend(loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.7)

# X축 눈금 조정
ax.set_xticks(x_vals)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "doe_yield_vs_temp.png")
plt.savefig(save_path, dpi=300)
plt.close()
