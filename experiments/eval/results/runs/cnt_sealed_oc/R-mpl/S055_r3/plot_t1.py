import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# 일자 컬럼 처리: 
# 1. 문자열 'yyyy-mm-dd' 또는 유사한 비유효 값이 섞여 있을 수 있음.
# 2. errors='coerce'를 사용하여 변환 실패 시 NaT로 만들고, 이를 기준으로 정렬하거나 제외하지 않되,
#    촉매로트의 순서를 결정하는 데 유효한 날짜만 사용함.
# 주의: preview에서 [날짜 2026-03-02~2026-08-30]라고 했으므로 대부분 정상일 가능성이 높으나,
# 헤더나 단위원(row)에 의해 첫 번째 행이 이상할 수 있음. read_excel은 보통 헤더를 자동으로 인식하지만,
# 혹시 모를 텍스트형 날짜 필드를 안전하게 datetime으로 변환합니다.
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# 등급 순서 정의
grade_order = ['A', 'B', 'C']

# 촉매로트별 등급 카운트 및 비율 계산
# 먼저 촉매로트를 시간순(가장 이른 일자 기준)으로 정렬하기 위한 기준값 생성
# 유효한 날짜가 있는 로트들의 최소 일자를 구함
lot_min_date = df.groupby('촉매로트')['일자'].min()

# 만약 어떤 로트에 유효한 날짜가 하나도 없다면(NaT), 해당 로트는 마지막에 배치하거나 임의 위치로 둠
# 여기서는 sort_values()가 NaT를 마지막에 두므로 별도 처리 불필요하나, 안전을 위해 dropna 고려 가능.
# 일단 sort_values 기본 동작(NaT last)을 따름.
lot_sorted = lot_min_date.sort_values().index.tolist()

# 피벗 테이블을 사용하여 각 로트별 등급 횟수 계산
pivot_counts = pd.crosstab(df['촉매로트'], df['등급'])

# 존재하지 않는 등급 컬럼이 있을 수 있으므로 재인덱싱
pivot_counts = pivot_counts.reindex(columns=grade_order, fill_value=0)

# 로트 순서에 맞춰 인덱스 정렬 (피벗 테이블에 없는 로트가 lot_sorted에 있으면 에러 방지용 intersection)
# 실제로는 crosstab된 index와 lot_sorted가 일치해야 함.
valid_lots = [l for l in lot_sorted if l in pivot_counts.index]
pivot_counts = pivot_counts.loc[valid_lots]
lot_sorted = valid_lots

# 총 개수로 나누어 비율(%) 계산
total_per_lot = pivot_counts.sum(axis=1)
pivot_percent = pivot_counts.div(total_per_lot, axis=0) * 100

# 플롯 그리기
fig, ax = plt.subplots(figsize=(12, 7))

bottom = np.zeros(len(pivot_percent))
colors = ['#4CAF50', '#FF9800', '#F44336'] # A: Green, B: Orange, C: Red

for i, grade in enumerate(grade_order):
    values = pivot_percent[grade].values
    bars = ax.bar(range(len(lot_sorted)), values, bottom=bottom, label=f'등급 {grade}', color=colors[i], edgecolor='white', width=0.8)
    
    # 막대 안에 텍스트 추가 (비율이 너무 작으면 생략 가능하지만, 여기서는 모두 표시하거나 조건부 표시)
    for j, (v, b) in enumerate(zip(values, bottom)):
        if v > 5: # 5% 이상일 때만 텍스트 표시하여 가독성 확보
            ax.text(j, b + v/2, f'{v:.1f}%', ha='center', va='center', color='white', fontsize=9, fontweight='bold')
    
    bottom += values

# 축 레이블 및 제목
ax.set_xticks(range(len(lot_sorted)))
ax.set_xticklabels(lot_sorted, rotation=45, ha='right')
ax.set_ylabel('비중 (%)')
ax.set_title('촉매로트별 등급(CNT 품질) 100% 누적 막대 그래프')
ax.legend(title='등급', loc='upper right', bbox_to_anchor=(1.15, 1), borderaxespad=0.)

# y축 범위 제한 (100% 스택 바 차트)
ax.set_ylim(0, 100)

# 격자선
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'grade_share_by_lot.png'), dpi=300, bbox_inches='tight')
plt.close(fig)
