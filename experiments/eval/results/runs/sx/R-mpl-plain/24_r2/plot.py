import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/24_r2/out"

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (첫 번째 시트 사용)
df = pd.read_excel(DATA_FILE, sheet_name=0)

# 열 이름 정리 (공백 제거 등)
df.columns = [col.strip() for col in df.columns]

# 필요한 열 추출
# X축: Temperature (°C)
# Y1축: Weight (%)
# Y2축: Heat Flow (W/g)
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Heat Flow (W/g)"

# 데이터가 존재하는지 확인
if x_col not in df.columns or y1_col not in df.columns or y2_col not in df.columns:
    raise ValueError(f"필요한 열({x_col}, {y1_col}, {y2_col}) 중 일부가 데이터에 없습니다.")

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 6))

# Y1축: Weight (%)
color1 = 'tab:blue'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1 = ax1.plot(df[x_col], df[y1_col], color=color1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# Y2축: Heat Flow (W/g)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Heat flow (W/g)', color=color2, fontsize=12)
line2 = ax2.plot(df[x_col], df[y2_col], color=color2, label='Heat flow (W/g)')
ax2.tick_params(axis='y', labelcolor=color2)

# 제목 설정
plt.title('TGA / DSC Analysis', fontsize=14)

# 범례 추가
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# 레이아웃 조정
plt.tight_layout()

# 파일 저장
output_path = os.path.join(OUT_DIR, "tga_heatflow.png")
plt.savefig(output_path, dpi=300)
plt.close(fig)
