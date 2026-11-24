import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 반응기별 등급 구성비 계산
# 등급 컬럼명 확인: '등급 (A/B/C)' 또는 유사한 이름일 수 있음. 미리보기에는 '등급 (A/B/C)'로 보이나 실제 컬럼명은 더러움.
# 미리보기: V 등급 (A/B/C) -> 컬럼명은 아마 '등급'이거나 공백이 포함될 수 있음. 안전하게 검색.
grade_col = [c for c in df.columns if '등급' in str(c)]
if not grade_col:
    raise ValueError("등급 컬럼을 찾을 수 없습니다.")
grade_col_name = grade_col[0]

reactor_col = [c for c in df.columns if '반응기' in str(c)][0]

# 크로스탭 생성: 행은 반응기, 열은 등급
ct = pd.crosstab(df[reactor_col], df[grade_col_name])

# 백분율 변환 (행 합 100%)
ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

# 순서 정렬 (R1, R2, R3, R4)
order = ['R1', 'R2', 'R3', 'R4']
# 존재하는 반응기만 필터링 및 정렬
existing_reactors = [r for r in order if r in ct_pct.index]
ct_pct = ct_pct.loc[existing_reactors]

# 그래프 그리기
fig, ax = plt.subplots(figsize=(8, 6))

# 묶음 막대 차트 (Grouped Bar Chart)
x = np.arange(len(existing_reactors))  # 라벨 위치
width = 0.25  # 막대 너비

grades = ['A', 'B', 'C']
colors = ['#4CAF50', '#FF9800', '#F44336'] # 초록, 주황, 빨강

for i, grade in enumerate(grades):
    if grade in ct_pct.columns:
        bars = ax.bar(x + i*width, ct_pct[grade], width, label=f'등급 {grade}', color=colors[i%3])
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=8)

ax.set_xlabel('반응기')
ax.set_ylabel('구성비 (%)')
ax.set_title('반응기별 CNT 등급(A/B/C) 구성비')
ax.set_xticks(x + width)
ax.set_xticklabels(existing_reactors)
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "reactor_grade_composition.png")
plt.savefig(output_filename, dpi=300)
plt.close()
