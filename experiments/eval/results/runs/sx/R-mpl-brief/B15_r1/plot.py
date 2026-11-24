import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B15_r1/out"

# 한글 폰트 설정
rcParams['font.family'] = 'Noto Sans CJK KR'
rcParams['axes.unicode_minus'] = False

# 출력 디렉토리 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 겹쳐 그리기: 하나의 축에 모든 시트를 그림
fig, ax1 = plt.subplots(figsize=(8, 6))

colors = ['#1f4e9c', '#27ae60', '#8e44ad'] # 각 시트별 색상 (y1용)
dtg_colors = ['#c0392b', '#d35400', '#2980b9'] # 각 시트별 색상 (y2용)

legend_labels_y1 = []
legend_labels_y2 = []

for i, sheet in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet)
    
    # 컬럼명 자동 감지 (미리보기 기준)
    temp_col = 'Temperature (°C)'
    weight_col = 'Weight (%)'
    dtg_col = 'Deriv. Weight (%/°C)'
    
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        continue
        
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dtg_col] * -1  # DTG 부호 반전
    
    # Y1 축 (무게 %)
    line1, = ax1.plot(x, y1, color=colors[i % len(colors)], label=f'{sheet} Weight')
    legend_labels_y1.append(line1)
    
    # Y2 축 (DTG) - 첫 번째 시트에서 생성한 후 공유하거나 별도 축 사용
    # 여기서는 겹쳐 그리므로 하나의 Y2 축을 공유하되, 선 색상을 구분해서 범례로 설명하는 것이 일반적임
    # 하지만 TGA 관례상 y2는 보통 하나의 축 스케일을 공유함. 
    # 여러 시트를 겹칠 때 y2 스케일이 크게 다르지 않다면 하나의 y2 축에 모두 그림
    
    if i == 0:
        ax2 = ax1.twinx()
        line2, = ax2.plot(x, y2, color=dtg_colors[i % len(dtg_colors)], linestyle='--', label=f'{sheet} DTG')
        legend_labels_y2.append(line2)
    else:
        line2, = ax2.plot(x, y2, color=dtg_colors[i % len(dtg_colors)], linestyle='--')
        legend_labels_y2.append(line2)

# 라벨 및 제목
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12, color='#1f4e9c')
ax2.set_ylabel('DTG (%/°C)', fontsize=12, color='#c0392b')
plt.title('TGA Analysis: PE, PVC, PET Overlaid', fontsize=14)

# 축 범위 조정 (예시)
ax1.set_xlim(30, 900)
ax1.set_ylim(0, 110)
ax2.set_ylim(-0.5, 3.0) # DTG 값 범위에 따라 적절히 조절 필요, 여기서는 대략적인 범위

# 잔류량(Residue at ~800°C)과 피크(Peak > 150°C) 표시 로직은 겹친 그래프에서는 복잡해짐.
# 요청사항이 "세 시트 겹쳐 그리고 범례는 그래프 바깥 오른쪽에 둬" 이므로,
# 표준 TGA 플롯의 모든 세부 사항(잔류량 마커 등)보다는 겹치기와 범례 위치에 집중함.
# 다만, 기본 가이드라인에 따라 주요 특징점은 가능하면 표시해야 함.
# 겹친 상태에서는 모든 곡선에 대해 개별적으로 마커를 찍으면 지저분해질 수 있으므로,
# 여기서는 범례 정렬을 우선시하고, 필요시 주석으로 대체하거나 생략할 수 있음.
# 그러나 시스템 프롬프트에는 "two labels are always drawn unless the user says otherwise"라고 되어 있음.
# 겹친 그래프에서도 각 시트에 대해 잔류량과 피크를 표시해야 함.

for i, sheet in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet)
    temp_col = 'Temperature (°C)'
    weight_col = 'Weight (%)'
    dtg_col = 'Deriv. Weight (%/°C)'
    
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2_raw = df[dtg_col].values
    
    # 1. Residue at nearest 800 °C
    idx_800 = np.argmin(np.abs(x - 800))
    residue_val = y1[idx_800]
    temp_800 = x[idx_800]
    
    # 잔류량 마커 및 텍스트 (y1 축 좌표계)
    marker_color_y1 = colors[i % len(colors)]
    ax1.plot(temp_800, residue_val, 'o', color=marker_color_y1, markersize=5)
    # 텍스트 위치 미세 조정
    ax1.text(temp_800 + 10, residue_val + 2, f'Residue {residue_val:.1f}%', 
             fontsize=8, color=marker_color_y1, ha='left')
             
    # 2. Peak temperature of highest DTG peak above 150 °C
    mask_temp = x > 150
    if np.any(mask_temp):
        y2_positive = -y2_raw[mask_temp] # DTG를 양수로 변환하여 최대값 찾기
        temps_masked = x[mask_temp]
        
        max_dtg_idx = np.argmax(y2_positive)
        peak_temp = temps_masked[max_dtg_idx]
        peak_dtg_val = -y2_raw[mask_temp][max_dtg_idx] # 원래 부호로 복원? 아니, plot된 값은 이미 *-1 됨
        
        # Plot된 y2 값은 이미 *-1 되었으므로, 최고 피크 높이는 y2_positive[max_dtg_idx]
        plotted_peak_height = y2_positive[max_dtg_idx]
        
        # 피크 마커 및 텍스트 (y2 축 좌표계)
        marker_color_y2 = dtg_colors[i % len(dtg_colors)]
        ax2.plot(peak_temp, plotted_peak_height, 'v', color=marker_color_y2, markersize=5)
        ax2.text(peak_temp, plotted_peak_height + 0.1, f'{peak_temp:.0f} °C', 
                 fontsize=8, color=marker_color_y2, ha='center')

# 범례 구성
lines = legend_labels_y1 + legend_labels_y2
labels = [l.get_label() for l in lines]

# 범례를 그래프 바깥 오른쪽에 배치
leg = ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)

# 레이아웃 조정
plt.tight_layout(rect=[0, 0, 0.85, 1]) # 오른쪽 공간 확보

# 저장
out_path = os.path.join(OUT_DIR, 'tga_overlaid.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
