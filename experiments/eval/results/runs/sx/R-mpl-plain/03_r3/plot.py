import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/03_r3/out"
SHEET_NAME = "1006R1-V acid"

# 폰트 설정 (한글 지원)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 열 이름 정리 (공백 제거 등)
df.columns = [col.strip() for col in df.columns]

# 필요한 컬럼 추출
# x: Temperature, y1: Weight(%), y2: D.W(%/C)
temp_col = 'Temperature'
weight_col = 'Weight(%)'
dw_col = 'D.W(%/C)'

if temp_col not in df.columns or weight_col not in df.columns or dw_col not in df.columns:
    # 대소문자나 약간의 차이 처리를 위해 유연하게 찾기
    cols = df.columns.tolist()
    temp_col = next((c for c in cols if 'temp' in c.lower()), None)
    weight_col = next((c for c in cols if 'weight' in c.lower()), None)
    dw_col = next((c for c in cols if 'd.w' in c.lower() or 'derivative' in c.lower()), None)

# 데이터 필터링 (x축 범위 100~800)
mask = (df[temp_col] >= 100) & (df[temp_col] <= 800)
df_filtered = df[mask].copy()

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 7))

# TGA 곡선 (Weight %)
color1 = 'tab:red'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1, = ax1.plot(df_filtered[temp_col], df_filtered[weight_col], color=color1, label='TGA')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xlim(100, 800)
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (D.W %/C) - 오른쪽 Y축 사용
ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
line2, = ax2.plot(df_filtered[temp_col], df_filtered[dw_col], color=color2, label='DTG')
ax2.tick_params(axis='y', labelcolor=color2)

# 피크 표시 (DTG의 최소값, 즉 무게 감소가 가장 빠른 지점)
# DTG 값이 음수이므로, 절대값이 큰 곳 또는 가장 낮은 값을 찾음
# find_peaks는 최대값을 찾으므로, -DTG를 사용하여 피크를 찾거나, 직접 최소값 인덱스를 찾음
dtg_values = df_filtered[dw_col].values
temps = df_filtered[temp_col].values

# 노이즈 제거 및 피크 검출을 위해 간단한 스무딩 적용 가능하지만, 여기서는 단순화
# DTG에서 가장 두드러진 2개의 피크(최소값)를 찾습니다.
# 방법: DTG 값이 음수인 구간에서 local minima를 찾음. 
# scipy.signal.find_peaks는 local maxima를 찾으므로, -dtg_values를 입력합니다.
# distance 파라미터로 너무 가까운 피크를 방지하고, prominence로 의미 있는 피크만 선택합니다.
peaks_indices, properties = find_peaks(-dtg_values, distance=50, prominence=0.1)

# 만약 피크가 2개 이상 발견되면, prominence 기준 상위 2개를 선택
if len(peaks_indices) > 2:
    prominences = properties['prominences']
    top_2_indices = np.argsort(prominences)[-2:]
    peaks_indices = peaks_indices[top_2_indices]
elif len(peaks_indices) < 2:
    # 피크가 부족하면 전체 중 최소값 2개를 수동으로 찾을 수도 있지만, 
    # 일반적으로 TGA에서는 명확한 피크가 있음. 
    # 안전장치: 최소값 인덱스 2개
    sorted_idx = np.argsort(dtg_values)[:2]
    peaks_indices = sorted_idx

# 피크 마커 및 텍스트 표시
for idx in peaks_indices:
    peak_temp = temps[idx]
    peak_dtg = dtg_values[idx]
    
    # 피크 위치 표시 (빨간색 별표 등)
    ax2.plot(peak_temp, peak_dtg, 'o', color='black', markersize=8, zorder=5)
    
    # 텍스트 레이블 (온도 표시)
    # y 위치는 피크 값보다 약간 아래나 위에 배치하여 가독성 확보
    text_y_offset = -0.05 * abs(min(dtg_values)) if min(dtg_values) != 0 else -0.05
    ax2.text(peak_temp, peak_dtg + text_y_offset, f'{peak_temp:.1f} °C', 
             horizontalalignment='center', verticalalignment='top', 
             fontsize=10, fontweight='bold', color='black')

# 범례 추가
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# 제목
plt.title(f'TGA/DTG Analysis: {SHEET_NAME}', fontsize=14)

# 레이아웃 조정
plt.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "tga_acid_plot.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
