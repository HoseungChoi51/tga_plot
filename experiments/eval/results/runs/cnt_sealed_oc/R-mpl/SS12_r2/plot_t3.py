import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# 일자 컬럼을 datetime으로 변환
df['일자'] = pd.to_datetime(df['일자'])

# 월 정보 추출 (YYYY-MM 형식)
df['월'] = df['일자'].dt.strftime('%Y-%m')

# 월별 원인별 정지시간 합계 계산 (Pivot table)
pivot_df = df.pivot_table(values='정지시간(분)', index='월', columns='원인', aggfunc='sum', fill_value=0)

# 월 순서대로 정렬
pivot_df = pivot_df.sort_index()

# 원인 열 순서를 전체 시간 기준으로 내림차순 정렬하여 스택의 시각적 우선순위 부여
cause_order = pivot_df.sum(axis=0).sort_values(ascending=False).index.tolist()
pivot_df = pivot_df[cause_order]

# 각 월별 총합으로 나누어 100% 정규화 (백분율)
total_by_month = pivot_df.sum(axis=1)
normalized_df = pivot_df.div(total_by_month, axis=0) * 100

# 플롯 생성
fig, ax = plt.subplots(figsize=(12, 7))

# 스택 바 차트 그리기
bottom = None
colors = ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#34495e', '#e67e22', '#1abc9c']

for i, cause in enumerate(normalized_df.columns):
    color = colors[i % len(colors)]
    
    # 막대 그리기
    bars = ax.bar(normalized_df.index, normalized_df[cause], bottom=bottom, label=cause, color=color, edgecolor='black')
    
    # 각 세그먼트의 값 표시 (백분율이므로 소수점 한 자리까지 표시)
    # 가독성을 위해 모든 세그먼트에 텍스트를 넣기보다는, 큰 부분만 넣거나 레전드로 대체할 수도 있음.
    # 여기서는 요청된 'Normalize' 결과를 명확히 보기 위해 각 블록 중앙에 백분율을 표시함.
    for bar in bars:
        height = bar.get_height()
        if height > 3:  # 너무 작은 블록은 생략
            y_pos = bar.get_y() + height / 2
            ax.text(bar.get_x() + bar.get_width() / 2, y_pos, f'{height:.1f}%', 
                    ha='center', va='center', fontsize=8, color='white', fontweight='bold')
    
    if bottom is not None:
        bottom = bottom + normalized_df[cause].values
    else:
        bottom = normalized_df[cause].values

# x축 라벨 회전
ax.set_xticks(range(len(normalized_df.index)))
ax.set_xticklabels(normalized_df.index, rotation=45, ha='right')

# y축 범위 설정 (0~100%)
ax.set_ylim(0, 100)

# 제목 및 레이블 설정
ax.set_title('월별 원인별 정지 시간 비율 (100% Stacked Bar Chart)', fontsize=14)
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('정지 시간 비중 (%)', fontsize=12)

# 레전드
ax.legend(title='원인', bbox_to_anchor=(1.05, 1), loc='upper left')

# 그리드
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "downtime_by_month_normalized.png")
plt.savefig(output_path, dpi=300)
plt.close()
