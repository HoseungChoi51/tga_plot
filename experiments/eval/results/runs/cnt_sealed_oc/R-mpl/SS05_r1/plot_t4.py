import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"
sheet_names = ["R3-260428-1", "R3-260810-2"]

# 색상 정의 (배치별 구분)
colors = ['tab:blue', 'tab:orange']

fig, ax1 = plt.subplots(figsize=(12, 7))
ax2 = ax1.twinx()

peak_info = {} # 피크 온도 및 값 저장용

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
    
    # 데이터 정제: dropna 후 인덱스 초기화하여 위치 기반 접근 시 오류 방지
    df_plot = df[[temp_col, weight_col, dwt_col]].dropna().reset_index(drop=True)
    
    x_temp_full = df_plot[temp_col].values
    y_dwt_full = df_plot[dwt_col].values
    y_weight_full = df_plot[weight_col].values
    
    # DTG 피크 검색: 미분중량이 최대인 지점
    # np.argmax가 반환하는 인덱스는 array의 실제 길이와 일치해야 함
    max_idx = int(np.argmax(y_dwt_full))
    
    # 안전장치: 인덱스가 유효한지 확인 (드물지만 데이터 정제 과정에서 발생 가능)
    if max_idx < len(x_temp_full):
        peak_temp = x_temp_full[max_idx]
        peak_val = y_dwt_full[max_idx]
        
        # x축 범위 400-800 내에 피크가 있는지 확인하여 텍스트 표시 여부 결정
        if 400 <= peak_temp <= 800:
            peak_info[sheet_name] = {'temp': peak_temp, 'val': peak_val}
        
    color = colors[i % len(colors)]
    
    # TG 곡선 (실선) - 좌측 Y축
    label_tg = f'{sheet_name} (TG)'
    line_tg = ax1.plot(x_temp_full, y_weight_full, color=color, linestyle='-', linewidth=1.5, label=label_tg)[0]
    
    # DTG 곡선 (점선) - 우측 Y축
    label_dtg = f'{sheet_name} (DTG)'
    line_dtg = ax2.plot(x_temp_full, y_dwt_full, color=color, linestyle='--', linewidth=1.5, alpha=0.7, label=label_dtg)[0]

# 축 설정
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('중량 (%)', fontsize=12)
ax1.grid(True, linestyle=':', alpha=0.5)
ax1.set_xlim(400, 800) # x축 범위 축소

ax2.set_ylabel('미분중량 (%/°C)', fontsize=12)
ax2.set_xlim(400, 800) # 우측 축도 동일 범위 적용

# DTG 피크 온도 표시 (텍스트 및 마커)
for i, sheet_name in enumerate(sheet_names):
    if sheet_name in peak_info:
        color = colors[i % len(colors)]
        p_data = peak_info[sheet_name]
        p_temp = p_data['temp']
        p_val = p_data['val']
        
        # ax2에 마커와 텍스트 표시
        ax2.scatter(p_temp, p_val, color=color, s=50, zorder=5, edgecolor='black')
        
        # 텍스트 위치 조정: 피크 위에 표시
        text_str = f'Peak: {p_temp:.1f} °C'
        # y좌표는 ax2 기준이므로 적절한 오프셋 추가
        offset_y = (ax2.get_ylim()[1] - ax2.get_ylim()[0]) * 0.05
        
        ax2.text(p_temp, p_val + offset_y, text_str, 
                 ha='center', va='bottom', fontsize=9, color=color, fontweight='bold',
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor=color, boxstyle='round,pad=0.3'))

# 범례 설정
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9)

plt.title(f'TGA 비교 분석: {", ".join(sheet_names)} (Range: 400-800°C)', fontsize=14)
fig.tight_layout()

# 저장
save_path = os.path.join(OUT_DIR, 'tga_comparison_R3_zoomed_peaks.png')
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
