import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# 컬럼 이름 확인 및 정규화 (공백 차이 등 고려)
cols = df_runs.columns.tolist()
target_col = None
for c in cols:
    if '가동시간' in str(c):
        target_col = c
        break

if target_col is None:
    raise ValueError("가동시간 컬럼을 찾을 수 없습니다.")

# 숫자형으로 변환
df_runs[target_col] = pd.to_numeric(df_runs[target_col], errors='coerce')

# 필터링: R1과 R4만 남김
df_filtered = df_runs[df_runs['반응기'].isin(['R1', 'R4'])]

# 그룹화하여 평균 계산: 반응기와 주차별 평균 가동시간
grouped_mean = df_filtered.groupby(['주차', '반응기'])[target_col].mean().reset_index()

# 피벗 테이블로 변환하여 그래프 그리기 쉽게 만듦
pivot_data = grouped_mean.pivot(index='주차', columns='반응기', values=target_col)

# 열 순서 보장 및 인덱스 정렬 (1~26)
all_weeks = list(range(1, 27))
pivot_data = pivot_data.reindex(columns=['R1', 'R4'], index=all_weeks)

# 플롯 그리기
fig, ax = plt.subplots(figsize=(10, 6))

colors = {'R1': '#1f77b4', 'R4': '#ff7f0e'} # 파랑색과 주황색 사용
markers = {'R1': 'o', 'R4': 's'}

for reactor in ['R1', 'R4']:
    ax.plot(pivot_data.index, pivot_data[reactor], 
            marker=markers[reactor], 
            linestyle='-', 
            color=colors[reactor], 
            label=f'{reactor} 평균 가동시간',
            linewidth=2,
            markersize=6)

# 제목 및 라벨
ax.set_title('R1 및 R4 반응기의 주차별 평균 가동시간 변화')
ax.set_xlabel('주차')
ax.set_ylabel('평균 가동시간 (h)')
ax.legend(loc='best')
ax.grid(True, linestyle='--', alpha=0.7)

# x축 눈금 간격 조정 (너무 빡빡하면 생략 가능하지만 여기서는 1~26이므로 모두 표시해도 됨. 필요시 step 조절)
ax.set_xticks(all_weeks)
# 만약 눈금이 겹치면 아래처럼 일부만 표시하거나 회전시킬 수 있음
# ax.set_xticks([w for w in all_weeks if w % 2 == 0]) 

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "line_plot_R1_R4_uptime.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
