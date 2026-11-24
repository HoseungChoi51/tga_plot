import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B21_r2/out"

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Raw 시트 데이터 읽기
df = pd.read_excel(DATA_FILE, sheet_name='Raw')

# x축(Temperature), y1(Weight), y2(Deriv. Weight) 추출
x = df['Temperature (°C)']
y1 = df['Weight (%)']
y2 = df['Deriv. Weight (%/°C)']

# 그래프 그리기
fig, ax1 = plt.subplots(figsize=(10, 6))

# TGA 곡선 (Weight %)
ax1.plot(x, y1, color='blue', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Weight (%)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

# x축 방향 뒤집기 (높은 온도가 왼쪽)
ax1.invert_xaxis()

# DTG 곡선 (Deriv. Weight %/°C) - 오른쪽 축 사용
ax2 = ax1.twinx()
ax2.plot(x, y2, color='red', linestyle='--', label='Deriv. Weight (%/°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# 범례 추가
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

# 제목 추가
plt.title('TGA/DTG Curves for Raw Sample')

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_raw_inverted.png")
plt.savefig(output_path, dpi=300)
plt.close()
