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
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# 열 이름 확인 및 정리 (공백 제거 등)
# 오류 메시지에 따르면 '등급 (A/B/C)'로 접근했으나 KeyError가 발생했습니다.
# 실제 컬럼명이 다르거나 공백이 있을 수 있으므로, 컬럼명을 명확히 합니다.
# 미리보기에서는 V 등급 (A/B/C) 로 표시되었지만, pandas에서 읽을 때 앞뒤 공백이나 특수문자 처리에 따라 다를 수 있습니다.
# 가장 안전한 방법은 컬럼명을 strip() 하여 비교하거나, 포함 여부를 체크하는 것입니다.

# 컬럼명 목록에서 '등급'을 포함하는 컬럼 찾기
grade_col = None
for col in df_runs.columns:
    if '등급' in str(col):
        grade_col = col
        break

if grade_col is None:
    # 만약 못 찾으면 미리보기에 나온 그대로 사용해보지만, 이번엔 이미 실패했으므로 다른 가능성 검토
    # 미리보기 텍스트를 신뢰하면 '등급 (A/B/C)'여야 함. 
    # 하지만 엑셀 파일의 헤더가 조금 다르게 파싱되었을 가능성이 높음.
    # 예를 들어 '등급' 만 있거나, 띄어쓰기가 다르면?
    # 일단 디버깅용 출력은 생략하고, 가장 유력한 후보인 '등급' 관련 컬럼을 재시도합니다.
    raise ValueError("등급 컬럼을 찾을 수 없습니다.")

reactor_col = '반응기' # 미리보기 E 반응기

# 반응기별 등급별 개수 세기
try:
    grade_counts = df_runs.groupby([reactor_col, grade_col]).size().unstack(fill_value=0)
except Exception as e:
    print(f"Groupby error with column '{grade_col}': {e}")
    # 혹시 컬럼명에 보이지 않는 문자가 있을까봐 리스트로 변환 후 매칭 시도
    unique_grades = df_runs[grade_col].unique()
    print(f"Unique grades found: {unique_grades}")
    raise e

# 각 반응기마다 합이 100%가 되도록 비율 계산 (%)
grade_percent = grade_counts.div(grade_counts.sum(axis=1), axis=0) * 100

# 정렬: 반응기 순서대로 (R1, R2, R3, R4)
reactor_order = ['R1', 'R2', 'R3', 'R4']
# 존재하지 않는 반응기는 제외하고 인덱스 재설정
valid_reactors = [r for r in reactor_order if r in grade_percent.index]
grade_percent = grade_percent.reindex(valid_reactors)

# 등급 순서 고정 (A, B, C) - 실제 데이터에 있는 값만 사용
available_grades = [g for g in ['A', 'B', 'C'] if g in grade_percent.columns]
grade_percent = grade_percent[available_grades]

# 막대 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 6))

bar_width = 0.8
x = np.arange(len(grade_percent.index))

# 묶인(bar group) 막대로 요청함
n_grades = len(available_grades)
if n_grades == 0:
    raise ValueError("No valid grades found in data.")

bar_width_group = bar_width / n_grades

colors = ['#2ecc71', '#f1c40f', '#e74c3c'] # A(초록), B(노랑), C(빨강) 등 구분을 위해
# 색상 가용성 체크
color_map = {'A': '#2ecc71', 'B': '#f1c40f', 'C': '#e74c3c'}

for i, grade in enumerate(available_grades):
    offset = (i - (n_grades - 1) / 2) * bar_width_group
    color = color_map.get(grade, 'gray')
    bars = ax.bar(x + offset, grade_percent[grade], width=bar_width_group, label=f'등급 {grade}', color=color)
    
    # 값 텍스트 추가
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9)

ax.set_xlabel('반응기')
ax.set_ylabel('구성비 (%)')
ax.set_title('반응기별 CNT 품질 등급 구성비')
ax.set_xticks(x)
ax.set_xticklabels(grade_percent.index)
ax.legend(title='품질 등급', loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_ylim(0, 105) # 여백 확보

plt.tight_layout()

output_path = os.path.join(OUT_DIR, "reactor_grade_distribution.png")
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Plot saved to {output_path}")
