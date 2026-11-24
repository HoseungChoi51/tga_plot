import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/13_r1/out"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (첫 번째 시트 사용)
df = pd.read_excel(DATA_FILE, sheet_name=0)

# 열 이름 정리 (공백 제거 등)
df.columns = df.columns.str.strip()

# 필요한 열 확인
# x축: Temperature (°C), y1축: Weight (mg)
x_col = "Temperature (°C)"
y1_col = "Weight (mg)"

# 데이터 정제 (NaN 제외)
plot_df = df[[x_col, y1_col]].dropna()

# 플롯 생성
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(plot_df[x_col], plot_df[y1_col], label='Weight', color='blue')

# 축 라벨 및 제목 설정
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (mg)', fontsize=12)
ax.set_title('TGA Curve: Weight vs Temperature', fontsize=14)

# 격자 표시
ax.grid(True, linestyle='--', alpha=0.6)

# 레전드 표시
ax.legend(loc='best')

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_weight_mg.png")
plt.savefig(output_path, dpi=300)
plt.close()
