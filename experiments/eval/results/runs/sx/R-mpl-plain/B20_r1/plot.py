import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# 파일 경로 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B20_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (Acid-washed 시트)
df = pd.read_excel(DATA_FILE, sheet_name='Acid-washed')

# 열 이름 확인 및 변수 할당
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
deriv_weight_col = 'Deriv. Weight (%/°C)'

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 6))

# TGA 곡선 (Weight %) - 왼쪽 Y축
line1 = ax1.plot(df[temp_col], df[weight_col], color='blue', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# DTG 곡선 (Deriv. Weight %/°C) - 오른쪽 Y축
ax2 = ax1.twinx()
line2 = ax2.plot(df[temp_col], df[deriv_weight_col], color='red', linestyle='--', label='Deriv. Weight (%/°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# x축에 보조 눈금(minor tick) 추가
ax1.xaxis.set_minor_locator(AutoMinorLocator())
ax1.tick_params(which='minor', length=4, color='black')

# 범례 추가
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# 제목
plt.title('TGA/DTG Analysis: Acid-washed Sample', fontsize=14)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = f"{OUT_DIR}/tga_acid_washed.png"
plt.savefig(output_path, dpi=300)
plt.close()
