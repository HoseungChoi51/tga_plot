import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 주차 컬럼이 문자열일 수 있으므로 숫자로 변환 (정수형으로 강제)
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
# NaN인 행 제거 (주차 정보가 없는 경우 등)
df = df.dropna(subset=['주차'])
df['주차'] = df['주차'].astype(int)

# 주차별로 등급(A, B, C)의 개수를 계산하기 위해 피벗 테이블 생성
grade_counts = df.pivot_table(index='주차', columns='등급', values='런ID', aggfunc='count', fill_value=0)

# 누락된 등급이 있을 수 있으므로 A, B, C 컬럼을 명시적으로 추가하고 0으로 채움
for grade in ['A', 'B', 'C']:
    if grade not in grade_counts.columns:
        grade_counts[grade] = 0

# 주차 순서 정렬 (숫자 오름차순)
grade_counts = grade_counts.sort_index()

# 시각화
fig, ax = plt.subplots(figsize=(12, 7))

colors = {'A': '#2ca02c', 'B': '#ff7f0e', 'C': '#d62728'} # 초록, 주황, 빨강
labels = ['A등급', 'B등급', 'C등급']
keys = ['A', 'B', 'C']

bottoms = np.zeros(len(grade_counts.index))

for key, label in zip(keys, labels):
    values = grade_counts[key].values
    ax.bar(grade_counts.index, values, bottom=bottoms, color=colors[key], label=label, width=0.8)
    bottoms += values

ax.set_title('주차별 CNT 생산 등급 분포', fontsize=16)
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('런 수 (개)', fontsize=12)
ax.legend(title='등급', loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_xticks(grade_counts.index)

# Y축 범위 조정
max_total = grade_counts.sum(axis=1).max()
ax.set_ylim(0, max_total * 1.15)

plt.tight_layout()
output_file = os.path.join(OUT_DIR, "grade_distribution_by_week.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
