import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B14_r3/out"
SHEET_NAME = "PVC"
FIG_WIDTH_INCHES = 10
FONT_SIZE = 16

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 컬럼명 확인 및 매핑 (미리보기 기준: B=Temperature, C=Weight, D=Deriv Weight)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
deriv_col = "Deriv. Weight (%/°C)"

# 데이터 추출
temperature = df[temp_col]
weight = df[weight_col]
deriv_weight = df[deriv_col]

# 플롯 생성
fig, ax1 = plt.subplots(figsize=(FIG_WIDTH_INCHES, FIG_WIDTH_INCHES * 0.75)) # 가로 10인치에 적절한 비율

# TGA 곡선 (Weight %) - 왼쪽 축
line1, = ax1.plot(temperature, weight, color='blue', linewidth=2, label='TGA (Weight %)')
ax1.set_xlabel('Temperature (°C)', fontsize=FONT_SIZE)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=FONT_SIZE)
ax1.tick_params(axis='y', labelcolor='blue', labelsize=FONT_SIZE)
ax1.tick_params(axis='x', labelsize=FONT_SIZE)
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (Deriv. Weight %/°C) - 오른쪽 축
ax2 = ax1.twinx()
line2, = ax2.plot(temperature, deriv_weight, color='red', linewidth=2, linestyle='--', label='DTG (Deriv. Weight %/°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red', fontsize=FONT_SIZE)
ax2.tick_params(axis='y', labelcolor='red', labelsize=FONT_SIZE)

# 범례 추가
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right', fontsize=FONT_SIZE)

# 제목
plt.title(f'TGA/DTG Analysis of {SHEET_NAME}', fontsize=FONT_SIZE + 2)

# 레이아웃 조정
plt.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, f"{SHEET_NAME}_TGA_Plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
