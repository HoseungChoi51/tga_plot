import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼 이름 공백 제거 및 매칭 (이전 오류 방지 로직 유지)
df.columns = df.columns.str.strip()

sample_col = None
reactor_col = None
catalyst_col = None
diameter_col = None

for col in df.columns:
    if '시료' in col or 'Sample' in col:
        sample_col = col
    elif '반응기' in col or 'Reactor' in col:
        reactor_col = col
    elif '촉매로트' in col or 'Catalyst' in col or 'Lot' in col:
        catalyst_col = col
    elif '직경' in col or 'Diameter' in col or 'nm' in col:
        diameter_col = col

# 만약 검색 실패 시 기본값 사용 (미리보기 기준 인덱스 활용)
if sample_col is None and len(df.columns) > 0:
    sample_col = df.columns[0] # A 시료
if reactor_col is None and len(df.columns) > 1:
    reactor_col = df.columns[1] # B 반응기
if catalyst_col is None and len(df.columns) > 2:
    catalyst_col = df.columns[2] # C 촉매로트
if diameter_col is None and len(df.columns) > 3:
    diameter_col = df.columns[3] # D 직경(nm)

print(f"Using Reactor Column: {reactor_col}, Catalyst Column: {catalyst_col}, Diameter Column: {diameter_col}")

# 그룹핑을 위한 새로운 라벨 컬럼 생성
# 예: 'R1 / FC-2604'
df['Label'] = df[reactor_col].astype(str) + ' / ' + df[catalyst_col].astype(str)

# 통계 계산: 평균과 표준편차
grouped_stats = df.groupby('Label')[diameter_col].agg(['mean', 'std']).reset_index()
grouped_stats.columns = ['Label', 'mean_diameter', 'std_diameter']

# 그래프 그리기
fig, ax = plt.subplots(figsize=(12, 7))

x_labels = grouped_stats['Label']
means = grouped_stats['mean_diameter']
stds = grouped_stats['std_diameter'].fillna(0) # NaN 처리

bars = ax.bar(x_labels, means, yerr=stds, capsize=5, color='skyblue', edgecolor='black', ecolor='red')

# 막대 위에 값 표시 (평균)
for bar, mean_val in zip(bars, means):
    height = bar.get_height()
    ax.annotate(f'{mean_val:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

ax.set_title('반응기/촉매로트별 TEM 직경 평균 및 표준편차', fontsize=14)
ax.set_xlabel('반응기 / 촉매로트', fontsize=12)
ax.set_ylabel('직경 (nm)', fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# X축 레이블 회전 (라벨이 길어질 수 있으므로)
plt.xticks(rotation=45, ha='right')

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tem_diameter_mean_std_reactor_catalyst.png')
plt.savefig(output_path, dpi=300)
plt.close()
