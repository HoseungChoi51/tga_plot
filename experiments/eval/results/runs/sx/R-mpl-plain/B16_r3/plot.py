import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B16_r3/out"

# 한글 폰트 설정 (Noto Sans CJK KR)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기
df = pd.read_csv(DATA_FILE)

# 필요한 열 추출
temperature = df['Temperature (°C)']
weight = df['Weight (%)']
dtg = df['Deriv. Weight (%/°C)']

# 그래프 그리기
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# 위쪽 그래프: TGA (무게 변화)
ax1.plot(temperature, weight, color='blue', label='TGA')
ax1.set_ylabel('무게 (%)')
ax1.set_title('TGA 및 DTG 분석 결과')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(loc='upper right')

# 아래쪽 그래프: DTG (미분 무게 변화)
ax2.plot(temperature, dtg, color='red', label='DTG')
ax2.set_xlabel('온도 (°C)')
ax2.set_ylabel('미분 무게 (%/°C)')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(loc='upper right')

# 레이아웃 조정
plt.tight_layout()

# 출력 파일 저장
output_path = os.path.join(OUT_DIR, "tga_dtg_plot.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')

print(f"그래프가 저장되었습니다: {output_path}")
