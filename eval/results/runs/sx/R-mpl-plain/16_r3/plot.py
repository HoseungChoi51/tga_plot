import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/16_r3/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (지정된 시트: "1006R1-V normal")
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal", header=0)

# X축과 Y축 데이터 추출
x_data = df['Temperature']
y_data = df['Weight(%)']

# 그래프 생성
fig, ax = plt.subplots(figsize=(8, 6))

# TGA 곡선 그리기 (무게만)
ax.plot(x_data, y_data, label='Weight (%)', color='blue', linewidth=2)

# 축 라벨 및 제목 설정
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (%)', fontsize=12)
ax.set_title('TGA Curve for 1006R1-V normal', fontsize=14)

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.7)

# 범례 표시
ax.legend(loc='best')

# 레이아웃 자동 조정
plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 그림 저장
output_path = os.path.join(OUT_DIR, "tga_normal_weight_only.png")
plt.savefig(output_path, dpi=300)

print(f"Graph saved to {output_path}")
