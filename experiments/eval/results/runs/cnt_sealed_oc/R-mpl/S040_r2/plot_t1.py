import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# 주차 컬럼이 문자열과 숫자가 섞여 있을 수 있으므로, 그룹화 전에 명확하게 처리하거나
# sort_index 시 타입 혼재로 인한 에러를 방지하기 위해 인덱스를 정수/문자 구분 없이 안전하게 변환하여 사용함.
# groupby 결과의 인덱스(주차)에 str과 int가 섞여 sort_index()에서 TypeError가 발생할 수 있음.
# 해결: 그룹핑 전 '주차' 컬럼을 모든 값이 비교 가능한 형태로 유지하되, 
# 더 안전한 방법은 피벗 후 인덱스를 명시적으로 정렬하는 로직을 수정하는 것임.

counts = df.groupby(['주차', '등급']).size().unstack(fill_value=0)

# 컬럼 순서 확립 (A, B, C) 및 누락된 등급이 있을 경우 0으로 채우기
expected_grades = ['A', 'B', 'C']
for grade in expected_grades:
    if grade not in counts.columns:
        counts[grade] = 0

counts = counts[expected_grades]

# 인덱스(주차)에 str과 int가 섞여 있을 때 sort_index()가 실패할 수 있으므로,
# 인덱스를 모두 문자열로 변환하여 일관성 있게 정렬합니다.
# 하지만 막대 그래프 x축 라벨은 보통 숫자 그대로 보이길 원하므로, 
# plotting 단계에서는 astype(str)를 사용하고, 정렬은 원래 숫자 값 기준으로 하되
# 인덱스의 타입 불일치를 제거하기 위해 index를 string으로 통일한 후 정렬하는 것이 안전합니다.
# 또는, pandas 버전 호환성을 위해 sort_values나 재인덱싱 방식을 쓸 수도 있습니다.
# 가장 간단한 수정: 인덱스를 str으로 변경하고 sort_index 호출.

counts.index = counts.index.astype(str)
counts = counts.sort_index()

# plotting
fig, ax = plt.subplots(figsize=(12, 6))

# stacked bar chart
bottoms = [0] * len(counts.index)
colors = ['#4CAF50', '#FFC107', '#F44336'] # Green for A, Yellow for B, Red for C

# 이제 counts.index는 모두 str이므로 직접 사용 가능
x_labels = counts.index.tolist()

for i, grade in enumerate(expected_grades):
    values = counts[grade].values
    ax.bar(x_labels, values, bottom=bottoms, label=f'등급 {grade}', color=colors[i], edgecolor='white')
    bottoms += values

# 라벨링
ax.set_xlabel('주차')
ax.set_ylabel('런 수 (개)')
ax.set_title('주차별 CNT 생산 등급 분포 (누적 막대 그래프)')
ax.legend(title='등급')

# x축 눈금 간격 조절
ax.set_xticks(range(len(x_labels)))
ax.set_xticklabels(x_labels, rotation=45, ha='right')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grade_distribution_by_week.png"), dpi=300)
plt.close()
