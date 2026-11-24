import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B10_r2/out"
SHEET_NAME = "Annealed"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 열 이름 확인 및 매핑 (미리보기 기준: B=Temperature, C=Weight, D=Deriv. Weight)
temp_col = df.columns[1]  # Temperature (°C)
weight_col = df.columns[2]  # Weight (%)
deriv_col = df.columns[3]  # Deriv. Weight (%/°C)

# 흑백 스타일 설정
line_style_weight = {'color': 'black', 'linewidth': 1.5, 'label': 'Weight (%)'}
line_style_deriv = {'color': 'black', 'linestyle': '--', 'linewidth': 1.5, 'label': 'Deriv. Weight (%/°C)'}

# 그림 생성
fig, ax1 = plt.subplots(figsize=(3.5, 2.6))

# TGA 곡선 (Weight %) - 왼쪽 Y축
ax1.plot(df[temp_col], df[weight_col], **line_style_weight)
ax1.set_xlabel('Temperature (°C)', fontsize=8)
ax1.set_ylabel('Weight (%)', fontsize=8, color='black')
ax1.tick_params(axis='y', labelcolor='black', labelsize=8)
ax1.tick_params(axis='x', labelsize=8)

# DTG 곡선 (Deriv. Weight) - 오른쪽 Y축
ax2 = ax1.twinx()
ax2.plot(df[temp_col], df[deriv_col], **line_style_deriv)
ax2.set_ylabel('Deriv. Weight (%/°C)', fontsize=8, color='black')
ax2.tick_params(axis='y', labelcolor='black', labelsize=8)

# 범례 추가
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=7, frameon=False)

# 레이아웃 조정
fig.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, f"{SHEET_NAME}_TGA.png")
plt.savefig(output_path, dpi=600, bbox_inches='tight')
plt.close()
