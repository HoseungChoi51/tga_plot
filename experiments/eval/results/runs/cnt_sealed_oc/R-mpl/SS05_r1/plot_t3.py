import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"
sheet_names = ["R3-260428-1", "R3-260810-2"]

# 색상 정의 (배치별 구분)
colors = ['tab:blue', 'tab:orange']

fig, ax1 = plt.subplots(figsize=(12, 7))
ax2 = ax1.twinx()

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 열 이름 확인 및 매핑
    cols = df.columns.tolist()
    temp_col = None
    weight_col = None
    dwt_col = None
    
    for c in cols:
        if '온도' in str(c):
            temp_col = c
        elif '중량 (%)' in str(c) or ('중량' in str(c) and '%' in str(c)):
            weight_col = c
        elif '미분중량' in str(c) or 'DTG' in str(c).upper():
            dwt_col = c
    
    if temp_col is None: temp_col = cols[1]
    if weight_col is None: weight_col = cols[2]
    if dwt_col is None: dwt_col = cols[3]
    
    # 데이터 정제
    df_plot = df[[temp_col, weight_col, dwt_col]].dropna()
    x_temp = df_plot[temp_col].values
    y_weight = df_plot[weight_col].values
    y_dwt = df_plot[dwt_col].values
    
    color = colors[i % len(colors)]
    
    # TG 곡선 (실선) - 좌측 Y축
    label_tg = f'{sheet_name} (TG)'
    line_tg = ax1.plot(x_temp, y_weight, color=color, linestyle='-', linewidth=1.5, label=label_tg)[0]
    
    # DTG 곡선 (점선) - 우측 Y축
    label_dtg = f'{sheet_name} (DTG)'
    line_dtg = ax2.plot(x_temp, y_dwt, color=color, linestyle='--', linewidth=1.5, alpha=0.7, label=label_dtg)[0]

# 축 설정
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('중량 (%)', fontsize=12)
ax1.grid(True, linestyle=':', alpha=0.5)

ax2.set_ylabel('미분중량 (%/°C)', fontsize=12)

# 범례 설정
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=9)

plt.title(f'TGA 비교 분석: {", ".join(sheet_names)}', fontsize=14)
fig.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'tga_comparison_R3_sheets.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
