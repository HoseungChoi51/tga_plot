import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-plain/10_r1/out"
os.makedirs(OUT_DIR, exist_ok=True)

# 폰트 설정 (한글 지원)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
xl = pd.ExcelFile(DATA_FILE)
sheets = xl.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 7))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
labels_map = {
    '1006R1-V normal': 'Normal',
    '1006R1-V acid': 'Acid-treated',
    '1006R1-V 750C': 'Calcined 750°C'
}

residual_data = []

for i, sheet in enumerate(sheets):
    # header=1로 읽어두면 첫 번째 행이 헤더가 됨. 
    # 하지만 일부 파일은 구조가 다를 수 있으므로 robust하게 처리하기 위해 
    # 먼저 header=None으로 읽고 직접 확인하거나, 기존 방식 유지하되 컬럼명 변환 시 에러 방지
    df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=1)
    
    # 컬럼명이 float인 경우(str 등)를 대비하여 str로 변환 후 strip
    new_columns = []
    for col in df.columns:
        if isinstance(col, str):
            new_columns.append(col.strip())
        else:
            new_columns.append(str(col).strip())
            
    df.columns = new_columns
    
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    
    # 컬럼이 없는 경우 대안 검색 (부분 일치 등)
    if temp_col not in df.columns:
        candidates = [c for c in df.columns if 'temp' in c.lower()]
        if candidates: temp_col = candidates[0]
        
    if weight_col not in df.columns:
        candidates = [c for c in df.columns if 'weight' in c.lower() or 'wt' in c.lower()]
        if candidates: weight_col = candidates[0]

    if temp_col not in df.columns or weight_col not in df.columns:
        continue
        
    temps = df[temp_col].values.astype(float)
    weights = df[weight_col].values.astype(float)
    
    label = labels_map.get(sheet, sheet)
    color = colors[i % len(colors)]
    
    # TGA 곡선 (좌측 Y축)
    ax1.plot(temps, weights, color=color, linewidth=2, label=f'{label} - TGA')
    
    # 700도에서의 잔류량 계산
    # 가장 가까운 온도점 찾기
    idx_700 = np.argmin(np.abs(temps - 700))
    temp_at_idx = temps[idx_700]
    weight_at_idx = weights[idx_700]
    
    residual_data.append({
        'label': label,
        'temp': temp_at_idx,
        'weight': weight_at_idx,
        'color': color
    })
    
    # DTG 곡선 (우측 Y축)
    dtg_col = None
    for c in df.columns:
        if 'd.w' in c.lower() or 'dtg' in c.lower():
            dtg_col = c
            break
            
    if dtg_col and dtg_col in df.columns:
        dtg = df[dtg_col].values.astype(float)
        ax2 = ax1.twinx()
        ax2.plot(temps, dtg, color=color, linestyle='--', alpha=0.3, linewidth=1)
        ax2.set_ylabel('DTG (%/°C)', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='gray')
        
        # 우측 축 상한 하한 조정하여 TGA가 잘 보이도록
        min_dtg = np.nanmin(dtg)
        max_dtg = np.nanmax(dtg)
        range_dtg = max_dtg - min_dtg
        if range_dtg == 0: range_dtg = 1
        ax2.set_ylim(min_dtg - range_dtg*0.1, max_dtg + range_dtg*0.1)

# 좌측 Y축 설정 (TGA)
ax1.set_xlabel('Temperature (°C)', fontsize=14)
ax1.set_ylabel('Weight (%)', fontsize=14)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_xlim(30, 900)
ax1.set_ylim(0, 105)

# 700 °C 기준선 및 잔류량 표시
ref_temp = 700
ax1.axvline(x=ref_temp, color='red', linestyle=':', linewidth=1.5, alpha=0.7, label='Reference Temp (700 °C)')

# 각 샘플의 700도에서의 잔류량 텍스트로 표시
for item in residual_data:
    # 점 표시
    ax1.plot(item['temp'], item['weight'], 'o', color=item['color'], markersize=8, markeredgecolor='black', zorder=5)
    
    # 텍스트 박스 위치 조정 (겹치지 않게 약간 오프셋)
    text_x = item['temp'] + 10
    text_y = item['weight'] + 5
    
    # 만약 오른쪽 끝이면 왼쪽으로 배치
    if text_x > 800:
        text_x = item['temp'] - 10
        ha = 'right'
    else:
        ha = 'left'
        
    txt = f"{item['label']}:\n{item['weight']:.2f} %"
    
    ax1.text(text_x, text_y, txt, 
             fontsize=10, 
             fontweight='bold',
             color=item['color'],
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=item['color'], alpha=0.8),
             horizontalalignment=ha,
             verticalalignment='bottom')

# 범례
lines, labels = ax1.get_legend_handles_labels()
ax1.legend(loc='upper right', fontsize=10)

plt.title('Thermogravimetric Analysis (TGA) with Residual Weight at 700 °C', fontsize=16, pad=15)

plt.tight_layout()

output_path = os.path.join(OUT_DIR, 'tga_residual_700C.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Saved plot to {output_path}")
