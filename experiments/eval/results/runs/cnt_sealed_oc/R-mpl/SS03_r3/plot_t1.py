import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 등급 컬럼명 확인 (데이터 미리보기상 'V 등급 (A/B/C)'로 보임)
grade_col = '등급' if '등급' in df.columns else [c for c in df.columns if '등급' in str(c)][0]
reactor_col = '반응기'

# 합격률 계산: A 또는 B인 경우를 1, 나머지(C 등)를 0으로 처리하여 평균 후 100을 곱함
df['is_pass'] = df[grade_col].isin(['A', 'B']).astype(int)
grouped = df.groupby(reactor_col)['is_pass'].mean() * 100
pass_rates = grouped.reset_index(name='합격률(%)')

# 순서 정렬 (R1~R4)
pass_rates.sort_values(by=reactor_col, inplace=True)

# 플롯 생성
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(pass_rates[reactor_col], pass_rates['합격률(%)'], color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])

# 값 라벨 추가
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{height:.1f}%',
            ha='center', va='bottom', fontsize=10)

ax.set_title('반응기별 합격률 (A·B 등급 비율)', fontsize=14)
ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel('합격률 (%)', fontsize=12)
ax.set_ylim(0, max(pass_rates['합격률(%)']) * 1.15) # y축 상단 여유
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "reactor_pass_rate.png")
plt.savefig(output_filename, dpi=300)
plt.close()
