import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 읽기
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# 일자 컬럼을 datetime으로 변환하고 월 추출
df['일자'] = pd.to_datetime(df['일자'])
df['월'] = df['일자'].dt.strftime('%Y-%m')

# 원인별 정지시간 합산 (월 x 원인 피벗 테이블)
pivot_table = df.pivot_table(index='월', columns='원인', values='정지시간(분)', aggfunc='sum', fill_value=0)

# 원인 순서를 전체 합계 기준 내림차순으로 정렬하여 스택 순서 결정
cause_order = pivot_table.sum(axis=0).sort_values(ascending=False).index.tolist()
pivot_table = pivot_table[cause_order]

# 차트 그리기
fig, ax = plt.subplots(figsize=(12, 7))
colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7']
bar_width = 0.8

bottom = pd.Series([0.0] * len(pivot_table.index), index=pivot_table.index)

for i, cause in enumerate(cause_order):
    color = colors[i % len(colors)]
    # 현재 원인의 값들
    current_vals = pivot_table[cause].values
    
    bars = ax.bar(pivot_table.index, current_vals, width=bar_width, bottom=bottom.values, label=cause, color=color, edgecolor='black')
    
    # 각 세그먼트 중앙에 값 표시
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            y_pos = bottom.iloc[j] + height / 2
            # 텍스트 색상 선택 (배경과 대비되게)
            text_color = 'white' if height > 50 else 'black'
            ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{int(height)}', ha='center', va='center', fontsize=8, color=text_color)
            
    # 다음 막대를 위해 bottom 업데이트
    bottom += pd.Series(current_vals, index=pivot_table.index)

ax.set_title("월별 및 원인별 총 정지 시간 (분)", fontsize=14)
ax.set_xlabel("월", fontsize=12)
ax.set_ylabel("총 정지 시간 (분)", fontsize=12)
ax.legend(title="원인", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.7)
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "downtime_by_month_cause.png")
plt.savefig(output_path, dpi=300)
plt.close()
