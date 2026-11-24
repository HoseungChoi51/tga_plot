import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B11_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (PET 시트)
df = pd.read_excel(DATA_FILE, sheet_name='PET')

# 열 이름 확인 및 매핑
# Time (min), Temperature (°C), Weight (%), Deriv. Weight (%/°C)
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
deriv_col = 'Deriv. Weight (%/°C)'

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 6))

# TGA 곡선 (무게 %) - 왼쪽 y축
ax1.plot(df[temp_col], df[weight_col], color='blue', label='TGA (Weight %)', linewidth=2)
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, linestyle='--', alpha=0.7)

# DTG 곡선 (미분 무게 %) - 오른쪽 y축
ax2 = ax1.twinx()
ax2.plot(df[temp_col], df[deriv_col], color='red', label='DTG (Deriv. Weight %/°C)', linewidth=2)
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# 제목 설정
plt.title('PET 열분해', fontsize=14, fontweight='bold')

# 범례 설정 (왼쪽 아래)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower left', fontsize=10)

# 레이아웃 조정
fig.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 그림 저장
output_path = os.path.join(OUT_DIR, 'PET_TGA.png')
plt.savefig(output_path, dpi=300)
plt.close()
