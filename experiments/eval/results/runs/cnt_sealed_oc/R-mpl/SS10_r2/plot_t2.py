import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# 시료별 평균 및 표준편차 계산
stats = df.groupby('시료')['직경(nm)'].agg(['mean', 'std']).reset_index()
stats.columns = ['시료', '평균_직경', '표준편차']

# 정렬 (막대 그래프 보기 좋게)
stats = stats.sort_values(by='시료').reset_index(drop=True)

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

x_pos = np.arange(len(stats['시료']))
bars = ax.bar(x_pos, stats['평균_직경'], yerr=stats['표준편차'], 
              capsize=5, color='skyblue', edgecolor='black', ecolor='red')

# 막대 위에 값 표시 (평균 ± 표준편차)
for i, bar in enumerate(bars):
    height = bar.get_height()
    std = stats.iloc[i]['표준편차']
    # 상단 오차막대 끝부분에 텍스트 배치 또는 중앙 배치 가능하나, 여기서는 막대 중심 높이 근처에 표시하거나
    # 오차막대 상단 위에 표시하는 것이 일반적입니다.
    error_top = height + std
    ax.annotate(f'{height:.2f} ± {std:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, error_top),
                xytext=(0, 3),  # 3 points vertical offset from top of error bar
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

# 라벨 및 제목
ax.set_xlabel('시료 (Sample)', fontsize=12)
ax.set_ylabel('평균 직경 (nm) ± 표준편차', fontsize=12)
ax.set_title('TEM 시료별 탄소나노튜브 직경 분포 (오차막대 포함)', fontsize=14)

# X축 눈금 라벨 설정
ax.set_xticks(x_pos)
ax.set_xticklabels(stats['시료'])

# Y축 범위 조절 (여백 추가)
max_val = (stats['평균_직경'] + stats['표준편차']).max()
ax.set_ylim(0, max_val * 1.2)

# 격자선
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'tem_mean_diameter_bar_with_std.png')
plt.savefig(save_path, dpi=300)
plt.close(fig)

print(f"그래프가 {save_path}에 저장되었습니다.")
