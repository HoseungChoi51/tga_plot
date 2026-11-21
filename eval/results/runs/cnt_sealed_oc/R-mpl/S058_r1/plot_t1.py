import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 로드
df_downtime = pd.read_excel("data/downtime.xlsx", sheet_name="정지이력")

# 노즐 막힘 이벤트만 필터링
df_nozzle_clog = df_downtime[df_downtime['원인'] == '노즐 막힘'].copy()

# 주 계산: week = (일자 − 2026-03-02) // 7 + 1
base_date = pd.to_datetime("2026-03-02")
df_nozzle_clog['일자'] = pd.to_datetime(df_nozzle_clog['일자'])
df_nozzle_clog['week'] = ((df_nozzle_clog['일자'] - base_date).dt.days // 7 + 1).astype(int)

# 피벗 테이블 생성: 행=반응기, 열=주, 값=개수
pivot_table = df_nozzle_clog.pivot_table(index='반응기', columns='week', values='일자', aggfunc='count')

# 결측치 0으로 채우기
pivot_table = pivot_table.fillna(0)

# 반응기 순서 정렬 (R1-R4)
reactor_order = ['R1', 'R2', 'R3', 'R4']
pivot_table = pivot_table.reindex(reactor_order)

# 주 순서 확인 및 필요시 재인덱스 (1~26주 전체 포함되도록)
all_weeks = list(range(1, 27))
pivot_table = pivot_table.reindex(columns=all_weeks, fill_value=0)

# 히트맵 플롯 (seaborn 없이 matplotlib imshow 사용)
fig, ax = plt.subplots(figsize=(14, 5))
im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto')

# Colorbar 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('Event Count', rotation=-90, va="bottom")

# 축 눈금 설정
ax.set_xticks(np.arange(len(all_weeks)))
ax.set_yticks(np.arange(len(reactor_order)))
ax.set_xticklabels([str(w) for w in all_weeks])
ax.set_yticklabels(reactor_order)

# x축 레이블 간격 조정 (가독성을 위해 2주마다 표시하거나 회전)
ax.set_xlabel('Production Week')
ax.set_ylabel('Reactor')
ax.set_title('Nozzle Clogging Events by Reactor and Production Week')

# 각 셀에 값 표시
for i in range(len(reactor_order)):
    for j in range(len(all_weeks)):
        text_color = "white" if pivot_table.values[i, j] > pivot_table.values.max() / 2 else "black"
        ax.text(j, i, int(pivot_table.values[i, j]), ha="center", va="center", color=text_color)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "nozzle_clog_heatmap.png")
plt.savefig(save_path, dpi=300)
plt.close()
