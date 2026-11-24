import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 경로 및 시트 이름
file_path = "data/tga_batches.xlsx"
sheets = ["R3-260428-1", "R3-260810-2"]

# 색상 정의
colors = ['blue', 'green'] # R3-260428-1: blue, R3-260810-2: green

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

all_tg_lines = []
all_dtg_lines = []

for i, sheet_name in enumerate(sheets):
    color = colors[i]
    
    # 데이터 읽기
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 컬럼명 확인 및 매핑
    cols = df.columns.tolist()
    temp_col = [c for c in cols if '온도' in str(c)][0]
    weight_col = [c for c in cols if '중량' in str(c) and '미분' not in str(c)][0]
    dtg_col = [c for c in cols if '미분' in str(c)][0]
    
    x = df[temp_col].values
    y_tg = df[weight_col].values
    y_dtg = df[dtg_col].values
    
    # TG 곡선 (좌측 Y축, 실선)
    line_tg, = ax1.plot(x, y_tg, color=color, linestyle='-', label=f'TG ({sheet_name})')
    all_tg_lines.append(line_tg)
    
    # DTG 곡선 (우측 Y축, 점선)
    line_dtg, = ax2.plot(x, y_dtg, color=color, linestyle='--', label=f'DTG ({sheet_name})')
    all_dtg_lines.append(line_dtg)
    
    # DTG 피크 계산 및 표시
    # 미분중량이 양수일 때의 최대값을 피크로 간주하거나, 절대값 기준일 수 있으나
    # 일반적으로 TGA에서 분해 속도가 가장 빠른 구간이 DTG의 극대점(Peak)임.
    # 미리보기 상 미분중량이 양수 범위가 주된 변동이므로 argmax 사용.
    max_dtg_idx = np.argmax(y_dtg)
    peak_temp = x[max_dtg_idx]
    peak_val = y_dtg[max_dtg_idx]
    
    # 피크 온도 텍스트 표시 (우측 축에 맞춤)
    ax2.annotate(f'{peak_temp:.1f}°C', 
                 xy=(peak_temp, peak_val), 
                 xytext=(5, 10), 
                 textcoords='offset points',
                 fontsize=9,
                 color=color,
                 ha='left', va='bottom',
                 arrowprops=dict(arrowstyle='->', color=color, lw=1.0))

# X축 범위 설정 (400 ~ 800 °C)
ax1.set_xlim(400, 800)

# 축 라벨 및 그리드
ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color='black')
ax1.grid(True, linestyle=':', alpha=0.5)

ax2.set_ylabel('미분중량 (%/°C)', color='black')

# 제목
plt.title(f'TG/DTG Curves Comparison: {", ".join(sheets)} (Zoomed 400-800°C)')

# 범례 처리
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

plt.tight_layout()

# 저장
output_filename = os.path.join(OUT_DIR, "TGA_R3_Comparison_Zoomed.png")
plt.savefig(output_filename, dpi=300)
print(f"Saved plot to {output_filename}")

plt.close(fig)
