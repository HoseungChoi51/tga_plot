import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 환경 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# 컬럼 이름 공백 제거 및 매칭 (이전 오류 방지 로직 유지)
df.columns = df.columns.str.strip()

sample_col = None
diameter_col = None

for col in df.columns:
    if '시료' in col or 'Sample' in col:
        sample_col = col
    if '직경' in col or 'Diameter' in col or 'nm' in col:
        diameter_col = col

# 만약 검색 실패 시 기본값 사용 (미리보기 기준 인덱스 활용)
if sample_col is None:
    sample_col = df.columns[0]
if diameter_col is None:
    # 미리보기에서 D 직경(nm)가 4번째 컬럼(C index 3)이라고 했으나, 실제 구조에 따라 다를 수 있어
    # 'nm' 또는 '직경'을 찾지 못했다면 가장 마지막 수치형 컬럼이나 적절한 인덱스를 고려해야 함.
    # 여기서는 미리보기 순서상 A,B,C,D 이므로 D는 인덱스 3번일 가능성이 높음.
    if len(df.columns) > 3:
        diameter_col = df.columns[3]
    else:
        raise ValueError("직경 컬럼을 찾을 수 없습니다.")

print(f"Using Sample Column: {sample_col}, Diameter Column: {diameter_col}")

# 통계 계산: 평균과 표준편차
grouped_stats = df.groupby(sample_col)[diameter_col].agg(['mean', 'std']).reset_index()
grouped_stats.columns = [sample_col, 'mean_diameter', 'std_diameter']

# 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

x_labels = grouped_stats[sample_col]
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
                ha='center', va='bottom', fontsize=10)

ax.set_title('시료별 TEM 직경 평균 및 표준편차', fontsize=14)
ax.set_xlabel('시료 (Sample)', fontsize=12)
ax.set_ylabel('직경 (nm)', fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tem_diameter_mean_std_bar.png')
plt.savefig(output_path, dpi=300)
plt.close()
