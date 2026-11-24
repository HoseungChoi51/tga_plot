import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# 시료별 평균 직경 계산
mean_diameters = df.groupby('시료')['직경(nm)'].mean().reset_index()

# 정렬 (막대 그래프 보기 좋게)
mean_diameters = mean_diameters.sort_values(by='시료')

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

bars = ax.bar(mean_diameters['시료'], mean_diameters['직경(nm)'], color='skyblue', edgecolor='black')

# 막대 위에 값 표시
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

# 라벨 및 제목
ax.set_xlabel('시료 (Sample)', fontsize=12)
ax.set_ylabel('평균 직경 (nm)', fontsize=12)
ax.set_title('TEM 시료별 평균 탄소나노튜브 직경', fontsize=14)

# Y축 범위 조절 (여백 추가)
max_val = mean_diameters['직경(nm)'].max()
ax.set_ylim(0, max_val * 1.15)

# 격자선
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'tem_mean_diameter_bar.png')
plt.savefig(save_path, dpi=300)
plt.close(fig)

print(f"그래프가 {save_path}에 저장되었습니다.")
