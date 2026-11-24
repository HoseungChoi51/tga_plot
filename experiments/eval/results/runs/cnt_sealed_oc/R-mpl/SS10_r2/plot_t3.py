import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# 라벨 생성: '반응기 / 촉매로트' 형식으로 결합
df['라벨'] = df['반응기'] + ' / ' + df['촉매로트']

# 시료 이름 대신 '반응기/촉매로트' 조합별 평균 및 표준편차 계산
stats = df.groupby('라벨')['직경(nm)'].agg(['mean', 'std']).reset_index()
stats.columns = ['라벨', '평균_직경', '표준편차']

# 정렬 (막대 그래프 보기 좋게, 알파벳/숫자 순서대로)
stats = stats.sort_values(by='라벨').reset_index(drop=True)

# 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 7)) # 가로폭을 넓혀 라벨 가독성 확보

x_pos = np.arange(len(stats['라벨']))
bars = ax.bar(x_pos, stats['평균_직경'], yerr=stats['표준편차'], 
              capsize=5, color='skyblue', edgecolor='black', ecolor='red')

# 막대 위에 값 표시 (평균 ± 표준편차)
for i, bar in enumerate(bars):
    height = bar.get_height()
    std = stats.iloc[i]['표준편차']
    error_top = height + std
    ax.annotate(f'{height:.2f} ± {std:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, error_top),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

# 라벨 및 제목
ax.set_xlabel('반응기 / 촉매로트', fontsize=12)
ax.set_ylabel('평균 직경 (nm) ± 표준편차', fontsize=12)
ax.set_title('TEM 탄소나노튜브 직경 분포 (반응기/촉매로트별)', fontsize=14)

# X축 눈금 라벨 설정
ax.set_xticks(x_pos)
ax.set_xticklabels(stats['라벨'], rotation=45, ha='right') # 라벨이 길어지므로 회전 적용

# Y축 범위 조절 (여백 추가)
max_val = (stats['평균_직경'] + stats['표준편차']).max()
ax.set_ylim(0, max_val * 1.2)

# 격자선
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'tem_mean_diameter_bar_by_reactor_catalyst.png')
plt.savefig(save_path, dpi=300)
plt.close(fig)

print(f"그래프가 {save_path}에 저장되었습니다.")
