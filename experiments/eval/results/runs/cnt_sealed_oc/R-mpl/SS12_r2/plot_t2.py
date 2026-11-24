import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# 일자 컬럼을 datetime으로 변환 (이미 날짜 형식이지만 명시적 변환 권장)
df['일자'] = pd.to_datetime(df['일자'])

# 월 정보 추출 (YYYY-MM 형식 또는 M월로 표시 가능하지만 스택 차트용으로는 정렬이 용이한 YYYY-MM 사용)
df['월'] = df['일자'].dt.strftime('%Y-%m')

# 월별 원인별 정지시간 합계 계산 (Pivot table)
pivot_df = df.pivot_table(values='정지시간(분)', index='월', columns='원인', aggfunc='sum', fill_value=0)

# 월 순서대로 정렬
pivot_df = pivot_df.sort_index()

# 원인 열 순서를 전체 시간 기준으로 내림차순 정렬하여 스택의 시각적 우선순위 부여
cause_order = pivot_df.sum(axis=0).sort_values(ascending=False).index.tolist()
pivot_df = pivot_df[cause_order]

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 7))

# 스택 바 차트 그리기
bottom = None
colors = ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#34495e', '#e67e22', '#1abc9c']

for i, cause in enumerate(pivot_df.columns):
    color = colors[i % len(colors)]
    bars = ax.bar(pivot_df.index, pivot_df[cause], bottom=bottom, label=cause, color=color, edgecolor='black')
    
    # 막대 위에 값 표시 (선택 사항: 너무 복잡할 수 있으므로 총합만 표시하거나 생략 가능하지만 요청에 따라 텍스트 추가 고려)
    # 여기서는 가독성을 위해 각 세그먼트의 중간 높이에는 값을 넣지 않고, 총합을 최상단에 표시하는 방식을 택하거나 그냥 레전드로 충분할 수 있음.
    # 하지만 사용자가 이전 턴에서 값 표시를 좋아했을 가능성이 있으므로, 각 스택의 가장 위쪽에 총합을 표시하는 것이 나을 수 있음.
    # 일단 기본 스택 차트를 그리고, 필요시 후처리
    
    if bottom is not None:
        bottom = bottom + pivot_df[cause].values
    else:
        bottom = pivot_df[cause].values

# x축 라벨 회전
ax.set_xticks(range(len(pivot_df.index)))
ax.set_xticklabels(pivot_df.index, rotation=45, ha='right')

# 제목 및 레이블 설정
ax.set_title('월별 원인별 정지 시간 분포 (Stacked Bar Chart)', fontsize=14)
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('정지 시간 (분)', fontsize=12)

# 레전드
ax.legend(title='원인', bbox_to_anchor=(1.05, 1), loc='upper left')

# 그리드
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "downtime_by_month_stacked.png")
plt.savefig(output_path, dpi=300)
plt.close()
