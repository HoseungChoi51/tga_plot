import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/16_r2/out"
SHEET_NAME = "1006R1-V normal"

# 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 열 이름 확인 (미리보기 기준: B=Temperature, C=Weight(%))
temp_col = 'Temperature'
weight_col = 'Weight(%)'

# 그래프 설정
plt.figure(figsize=(8, 6))
plt.plot(df[temp_col], df[weight_col], label='Weight (%)', color='blue')

# 축 라벨 및 제목 설정
plt.xlabel('Temperature (°C)', fontsize=12)
plt.ylabel('Weight (%)', fontsize=12)
plt.title(f'TGA Curve - {SHEET_NAME}', fontsize=14)

# 그리드 및 범례 표시
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# 레이아웃 조정
plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 파일 저장
output_path = os.path.join(OUT_DIR, "tga_normal_weight.png")
plt.savefig(output_path, dpi=300)

# 플롯 닫기
plt.close()
