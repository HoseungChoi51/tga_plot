import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B11_r3/out"
SHEET_NAME = "PET"
TITLE = "PET 열분해"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 컬럼명 확인 및 매핑 (미리보기 기준: B=Temperature, C=Weight, D=Deriv Weight)
# 실제 컬럼명이 공백이나 특수문자를 포함할 수 있으므로 strip 처리 권장되나, 미리보기와 일치한다고 가정
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
deriv_col = "Deriv. Weight (%/°C)"

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(8, 6))

# TGA 곡선 (무게 %) - 왼쪽 Y축
line1 = ax1.plot(df[temp_col], df[weight_col], label='Weight (%)', color='blue')
ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Weight (%)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# DTG 곡선 (미분 무게) - 오른쪽 Y축
ax2 = ax1.twinx()
line2 = ax2.plot(df[temp_col], df[deriv_col], label='Deriv. Weight (%/°C)', color='red')
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# 제목
ax1.set_title(TITLE)

# 격자 켜기
ax1.grid(True, linestyle='--', alpha=0.7)

# 범례 왼쪽 아래 배치
# 두 축의 핸들과 라벨을 합쳐서 하나의 범례로 만듦
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower left')

# 출력 디렉토리 생성
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "pet_tga.png")

# 저장 (300 dpi)
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
