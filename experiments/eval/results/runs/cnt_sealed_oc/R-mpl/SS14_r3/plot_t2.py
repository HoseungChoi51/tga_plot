import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t2"
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

# 에러 원인 해결: dtype->object로 인해 mean 실패. 
# 문자열이 섞여 있을 가능성이 높으므로 숫자로 강제 변환 후 NaN 처리
df_runs[target_col] = pd.to_numeric(df_runs[target_col], errors='coerce')

# 피벗 테이블 생성: 반응기별 주차별 평균 가동시간
pivot_mean = df_runs.pivot_table(index='반응기', columns='주차', values=target_col, aggfunc='mean')

# 열 순서 고정 (1~26)
all_weeks = list(range(1, 27))
pivot_mean = pivot_mean.reindex(columns=all_weeks)

# 행 순서 고정 (R1~R4)
reactors = ['R1', 'R2', 'R3', 'R4']
pivot_mean = pivot_mean.reindex(index=reactors)

# Heatmap 그리기
fig, ax = plt.subplots(figsize=(12, 5))

# heatmap 데이터: numpy array로 변환
heatmap_data = pivot_mean.values

# imshow 사용
im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')

# 눈금 라벨 설정
ax.set_xticks(np.arange(len(all_weeks)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels(all_weeks)
ax.set_yticklabels(reactors)

# 셀마다 수치 표시 (소수점 1자리)
vmin = np.nanmin(heatmap_data)
vmax = np.nanmax(heatmap_data)
mid = (vmin + vmax) / 2

for i in range(len(reactors)):
    for j in range(len(all_weeks)):
        val = heatmap_data[i, j]
        
        # NaN 처리
        if np.isnan(val):
            text_str = ""
            color = 'black'
        else:
            text_str = f"{val:.1f}"
            # 컬러 매핑에 따른 텍스트 색상 결정
            color = 'white' if val > mid else 'black'
            
        ax.text(j, i, text_str, ha='center', va='center', color=color, fontsize=8)

# 컬러바 추가
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 가동시간 (h)', rotation=-90, va="bottom")

# 제목 및 라벨
ax.set_title('반응기별 주차별 평균 가동시간 Heatmap')
ax.set_xlabel('주차')
ax.set_ylabel('반응기')

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "heatmap_run_count.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
