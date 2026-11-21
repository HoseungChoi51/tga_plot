import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B10_r2/out"
SHEET_NAME = "Annealed"

# 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 열 이름 확인 및 변수 할당 (전제: B=Temperature, C=Weight, D=Deriv Weight)
# 데이터 미리보기에 따르면:
# A: Time (min), B: Temperature (°C), C: Weight (%), D: Deriv. Weight (%/°C)
temp_col = [c for c in df.columns if 'Temperature' in c][0]
weight_col = [c for c in df.columns if 'Weight (%)' in c or 'Weight' in c][0]
dtg_col = [c for c in df.columns if 'Deriv' in c or 'DTG' in c][0]

temperature = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# DTG 부호 반전 (피크가 위로 가도록)
dtg_inv = -dtg

# 그림 생성
fig, ax1 = plt.subplots(figsize=(3.5, 2.6))

# 흑백 스타일 설정
line_color_y1 = 'black'
line_color_y2 = 'gray' # 또는 점선 등으로 구분 가능하나 요청은 흑백이므로 회색 사용하거나 점선 활용 가능. 일반적으로 축 구분을 위해 선 종류나 색조 차이를 둠. 여기서는 y1은 실선 검정, y2는 점선 회색으로 구분하는 것이 논문에서 흔함. 하지만 단순히 "흑백"이면 모두 검정이나 회조로 처리. 명확성을 위해 y1은 solid black, y2는 dashed gray/black로 가되, 범례와 라벨 크기 조절.
# 더 엄격한 흑백(모노톤)을 위해 y1: solid black, y2: dashed black 또는 gray.
# 보통 TGA에서 두 곡선을 구분하기 위해 y1은 solid, y2는 dashed를 많이 씁니다.
line_style_y1 = '-'
line_style_y2 = '--'
color_y1 = 'k'
color_y2 = 'k' # 또는 '0.5'

ax1.plot(temperature, weight, color=color_y1, linestyle=line_style_y1, label='Weight (%)', linewidth=1.2)
ax1.set_xlabel('Temperature (°C)', fontsize=8)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=8)
ax1.tick_params(axis='y', labelcolor=color_y1, labelsize=8)
ax1.tick_params(axis='x', labelsize=8)

ax2 = ax1.twinx()
ax2.plot(temperature, dtg_inv, color=color_y2, linestyle=line_style_y2, label='DTG (-%/°C)', linewidth=1.2)
ax2.set_ylabel('DTG (-%/°C)', color=color_y2, fontsize=8)
ax2.tick_params(axis='y', labelcolor=color_y2, labelsize=8)

# 제목
ax1.set_title(SHEET_NAME, fontsize=9) # 제목 크기는 본문보다 약간 크게 하거나 동일하게 유지 가능. 요청에는 글자 크기 8이라고 했으므로 전체 기본값을 8로 하고 제목만 조정하거나, 모든 텍스트를 8로 맞출 수 있음. 여기서는 축라벨과 틱을 8로 맞춤.

# 잔류량(Residue) 계산 및 표시 (800°C 근처)
idx_800 = np.argmin(np.abs(temperature - 800))
residue_weight = weight[idx_800]
residue_temp = temperature[idx_800]

# 피크(Peak) 계산 및 표시 (150°C 이상 DTG 최고점)
mask = temperature > 150
if mask.any():
    dtg_masked = dtg_inv[mask]
    temp_masked = temperature[mask]
    idx_peak_local = np.argmax(dtg_masked)
    peak_temp = temp_masked[idx_peak_local]
    peak_dtg_val = dtg_masked[idx_peak_local]
else:
    peak_temp = None
    peak_dtg_val = None

# 마커 및 라벨 추가
# Residue Marker on Weight Curve (ax1)
ax1.plot(residue_temp, residue_weight, 'o', color=color_y1, markersize=4)
ax1.annotate(f'Residue {residue_weight:.1f}%', 
             xy=(residue_temp, residue_weight), 
             xytext=(10, 10), textcoords='offset points',
             fontsize=8, color=color_y1,
             arrowprops=dict(arrowstyle='->', color=color_y1, lw=0.8))

# Peak Marker on DTG Curve (ax2)
if peak_temp is not None:
    ax2.plot(peak_temp, peak_dtg_val, 'v', color=color_y2, markersize=4)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_dtg_val), 
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=8, color=color_y2,
                 arrowprops=dict(arrowstyle='->', color=color_y2, lw=0.8))

# 범례 위치: center left
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=7, frameon=False)

# 격자 제거 (논문용 깔끔한 느낌)
ax1.grid(False)
ax2.grid(False)

# 레이아웃 조정
plt.tight_layout()

# 저장
out_path = Path(OUT_DIR)
out_path.mkdir(parents=True, exist_ok=True)
save_file = out_path / f"{SHEET_NAME}_bw.png"
plt.savefig(save_file, dpi=600, bbox_inches='tight')
plt.close()
