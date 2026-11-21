import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/15_r3/out"
os.makedirs(OUT_DIR, exist_ok=True)

# 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 색상 정의 (시트별 구분용)
colors_y1 = ['#1f4e9c', '#2ecc71', '#8e44ad', '#e67e22', '#34495e']
colors_y2 = ['#c0392b', '#d35400', '#9b59b6', '#f39c12', '#2c3e50']

fig, ax1 = plt.subplots(figsize=(10, 7))
ax2 = ax1.twinx()

max_temp_global = 0
min_weight_global = 100
max_dtg_global = 0 # DTG is negative, so we look for min value (most negative) to scale y2 properly if needed, but usually auto-scale is fine. 
                   # However, since we plot -DTG, we want max of (-DTG).

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 컬럼명 자동 감지 (미리보기 기반: B=Temperature, C=Weight(%), D=D.W(%/C))
    temp_col = None
    weight_col = None
    dtg_col = None
    
    cols = df.columns.tolist()
    for col in cols:
        c_lower = str(col).lower()
        if 'temp' in c_lower or 'temperature' in c_lower:
            temp_col = col
        elif 'weight' in c_lower and '%' in str(col):
            weight_col = col
        elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower:
            dtg_col = col
            
    # 폴백: 위치 기반 (B, C, D -> index 1, 2, 3 assuming A is time/index)
    if temp_col is None and len(cols) > 1: temp_col = cols[1]
    if weight_col is None and len(cols) > 2: weight_col = cols[2]
    if dtg_col is None and len(cols) > 3: dtg_col = cols[3]

    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].dropna().values
    y1 = df[weight_col].dropna().values
    y2_raw = df[dtg_col].dropna().values
    
    # 길이 맞춤
    min_len = min(len(x), len(y1), len(y2_raw))
    x = x[:min_len]
    y1 = y1[:min_len]
    y2_raw = y2_raw[:min_len]
    
    # DTG 부호 반전 (피크가 위로 가도록)
    y2_plot = -y2_raw
    
    # 전역 범위 업데이트
    max_temp_global = max(max_temp_global, np.max(x))
    min_weight_global = min(min_weight_global, np.min(y1))
    
    # 색상 선택
    color1 = colors_y1[i % len(colors_y1)]
    color2 = colors_y2[i % len(colors_y2)]
    
    # 플롯 그리기
    line1, = ax1.plot(x, y1, color=color1, label=f'{sheet_name} Weight', linewidth=1.5)
    line2, = ax2.plot(x, y2_plot, color=color2, linestyle='--', label=f'{sheet_name} DTG', linewidth=1.2, alpha=0.8)
    
    # 라벨 계산: Residue at ~800°C
    target_temp_residue = 800.0
    idx_residue = np.argmin(np.abs(x - target_temp_residue))
    residue_val = y1[idx_residue]
    residue_temp = x[idx_residue]
    
    # 라벨 계산: Peak temperature (>150°C)
    mask_peak = x > 150.0
    if np.any(mask_peak):
        x_peak_range = x[mask_peak]
        y2_peak_range = y2_plot[mask_peak] # Already inverted
        
        # Find highest peak
        max_idx_local = np.argmax(y2_peak_range)
        peak_temp = x_peak_range[max_idx_local]
        peak_val = y2_peak_range[max_idx_local]
        
        # 마커 및 텍스트 표시
        # Residue Marker on Y1 curve
        ax1.scatter([residue_temp], [residue_val], color=color1, s=50, zorder=5, edgecolors='black', linewidth=0.5)
        # Offset text slightly to avoid overlap
        offset_x = 10
        offset_y = 2
        ax1.text(residue_temp + offset_x, residue_val + offset_y, f'Residue {residue_val:.1f}%', 
                 fontsize=8, color=color1, ha='left', va='bottom')
                 
        # Peak Marker on Y2 curve
        ax2.scatter([peak_temp], [peak_val], color=color2, s=50, marker='v', zorder=5, edgecolors='black', linewidth=0.5)
        ax2.text(peak_temp, peak_val + 0.05, f'{peak_temp:.0f} °C', 
                 fontsize=8, color=color2, ha='center', va='bottom')

# 축 설정
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12, color='#333333')
ax2.set_ylabel('DTG (%/°C)', fontsize=12, color='#333333')

# 범례 합치기
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
all_lines = lines_1 + lines_2
all_labels = labels_1 + labels_2

# 레이블이 너무 많으면 그룹화하거나 생략할 수 있지만, 여기서는 전부 표시
legend = ax1.legend(all_lines, all_labels, loc='center left', bbox_to_anchor=(0.02, 0.5), fontsize=9, framealpha=0.9)

# 제목
plt.title('TGA Analysis: All Sheets Overlay', fontsize=14)

# 격자
ax1.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()

# 저장
out_path = os.path.join(OUT_DIR, "TGA_all_sheets_overlay.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Plot saved to {out_path}")
