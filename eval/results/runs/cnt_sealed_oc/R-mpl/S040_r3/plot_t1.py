import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 주차별 등급 개수 집계
# pivot_table을 사용하여 행은 주차, 열은 등급으로 만들고 개수를 셈
grade_counts = df.pivot_table(index='주차', columns='등급', values='런ID', aggfunc='count').fillna(0).astype(int)

# 열 순서 고정 (A, B, C) - 만약 데이터에 없는 등급이 있을 수 있으므로 재인덱싱 처리
columns_order = ['A', 'B', 'C']
for col in columns_order:
    if col not in grade_counts.columns:
        grade_counts[col] = 0
grade_counts = grade_counts[columns_order]

# 정렬 확인 (주차 오름차순)
# 주차 컬럼이 숫자가 아닌 문자열일 경우를 대비해 int로 변환하여 정렬 후 인덱스를 업데이트함
try:
    # 기존 인덱스(주차)를 숫자로 변환 시도
    temp_index = pd.to_numeric(grade_counts.index, errors='coerce')
    
    # 변환된 값 기준으로 정렬
    sort_idx = temp_index.argsort()
    grade_counts = grade_counts.iloc[sort_idx]
    
    # 인덱스도 숫자 타입으로 정리해서 플롯 시 깔끔하게 표시되도록 함
    grade_counts.index = pd.to_numeric(grade_counts.index, errors='coerce')
except Exception:
    # 실패 시 원본 인덱스 유지 (문자열 등)
    pass

# 플롯 그리기
fig, ax = plt.subplots(figsize=(12, 7))

# 누적 막대 그래프를 위해 각 시리즈의 시작 위치 계산
bottoms = [0] * len(grade_counts.index)
colors = ['#FFD700', '#4682B4', '#CD5C5C'] # A: 노랑계열, B: 파랑계열, C: 빨강계열 등 구분되는 색상
labels = ['A 등급', 'B 등급', 'C 등급']

x_values = grade_counts.index.tolist()

for i, col in enumerate(columns_order):
    ax.bar(x_values, grade_counts[col], bottom=bottoms, label=labels[i], color=colors[i], edgecolor='black')
    bottoms += grade_counts[col].values

# 라벨 및 제목
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('런 횟수 (개)', fontsize=12)
ax.set_title('주차별 CNT 생산 등급 분포 (누적 막대그래프)', fontsize=14)
ax.legend(title='등급', loc='upper right')

# x축 눈금 간격 조절 (주차가 많으므로 모든 주차를 표시하기보다는 적절한 간격으로 또는 회전해서 표시)
if len(x_values) > 0:
    try:
        max_week = max([int(v) for v in x_values if str(v).isdigit()])
        ticks = range(1, max_week + 1)
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(t) for t in ticks], rotation=90, fontsize=8)
    except:
        # 숫자 처리가 안 되면 그냥 현재 인덱스 사용
        ax.set_xticks(x_values)
        ax.set_xticklabels([str(v) for v in x_values], rotation=90, fontsize=8)

plt.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, "grade_distribution_by_week.png")
plt.savefig(save_path, dpi=300)
plt.close()
