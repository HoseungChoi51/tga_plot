import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B10_r3/out"
SHEET_NAME = "Annealed"
FIG_WIDTH_INCHES = 3.5
FIG_HEIGHT_INCHES = 2.6
DPI = 600
FONT_SIZE = 8

# 폰트 설정 (한글 지원)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, header=0)

# 컬럼 이름 확인 및 매핑
cols = df.columns.tolist()
# 예상: ['Time (min)', 'Temperature (°C)', 'Weight (%)', 'Deriv. Weight (%/°C)']
try:
    temp_col = [c for c in cols if 'Temperature' in c][0]
    weight_col = [c for c in cols if 'Weight (%)' in c and 'Deriv' not in c][0]
    deriv_col = [c for c in cols if 'Deriv' in c or 'dW/dT' in c.lower()][0]
except IndexError:
    # 폴백: 위치 기반
    temp_col = cols[1]
    weight_col = cols[2]
    deriv_col = cols[3]

temp = df[temp_col]
weight = df[weight_col]
deriv = df[deriv_col]

# 흑백 스타일 설정
plt.style.use('grayscale')

fig, ax1 = plt.subplots(figsize=(FIG_WIDTH_INCHES, FIG_HEIGHT_INCHES))

# TGA 곡선 (Left Axis)
ax1.plot(temp, weight, color='black', linewidth=1.0, label='Weight %')
ax1.set_xlabel('Temperature (°C)', fontsize=FONT_SIZE)
ax1.set_ylabel('Weight (%)', fontsize=FONT_SIZE)
ax1.tick_params(axis='both', which='major', labelsize=FONT_SIZE)
ax1.set_xlim(30, 900)
ax1.set_ylim(0, 105)

# DTG 곡선 (Right Axis)
ax2 = ax1.twinx()
ax2.plot(temp, deriv, color='black', linestyle='--', linewidth=1.0, label='DTG')
ax2.set_ylabel('Deriv. Weight (%/°C)', fontsize=FONT_SIZE)
ax2.tick_params(axis='y', which='major', labelsize=FONT_SIZE)
# DTG 축 범위 조정 (음수 값이 주를 이룸)
ax2.set_ylim(-1.5, 0.5)

# 레전드 생성
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', fontsize=FONT_SIZE, frameon=False)

# 그리드
ax1.grid(True, linestyle=':', alpha=0.5)

# 레이아웃 조절
plt.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "tga_annealed_bw.png")
plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
plt.close()
