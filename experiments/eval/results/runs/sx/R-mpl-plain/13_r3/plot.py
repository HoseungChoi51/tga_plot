import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/13_r3/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

# 데이터 읽기 (첫 번째 시트 사용)
df = pd.read_excel(DATA_FILE, sheet_name=0)

# X축과 Y축 데이터 추출
# X축: Temperature (°C), Y축: Weight (mg)
x_col = 'Temperature (°C)'
y_col = 'Weight (mg)'

# 그래프 생성
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(df[x_col], df[y_col], color='blue', linewidth=1.5)

# 축 라벨 및 제목 설정
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (mg)', fontsize=12)
ax.set_title('TGA Curve', fontsize=14)

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.7)

# 레이아웃 자동 조정
plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 그림 저장
output_path = os.path.join(OUT_DIR, 'tga_weight_mg.png')
plt.savefig(output_path, dpi=300)
plt.close()
