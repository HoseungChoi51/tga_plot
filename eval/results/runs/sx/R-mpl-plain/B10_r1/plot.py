import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B10_r1/out"

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Excel 파일 읽기 (Annealed 시트만 사용)
try:
    df = pd.read_excel(DATA_FILE, sheet_name='Annealed')
except Exception as e:
    raise ValueError(f"데이터를 읽는 중 오류가 발생했습니다: {e}")

# 필요한 컬럼 추출
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
deriv_col = 'Deriv. Weight (%/°C)'

if temp_col not in df.columns or weight_col not in df.columns or deriv_col not in df.columns:
    raise KeyError("필요한 컬럼(Temperature, Weight, Deriv. Weight)을 찾을 수 없습니다.")

temperature = df[temp_col]
weight = df[weight_col]
deriv_weight = df[deriv_col]

# 그림 크기 및 dpi 설정
fig_width = 3.5
fig_height = 2.6
dpi = 600

# 흑백 스타일 적용을 위해 grayscale colormap 또는 명시적 색상 지정
# 논문용 흑백 플롯: TGA 곡선은 실선, DTG 곡선은 점선 등으로 구분하는 것이 일반적임
fig, ax1 = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)

# TGA 곡선 (좌측 Y축): 검은색 실선
ax1.plot(temperature, weight, color='black', linestyle='-', linewidth=1.2, label='TGA')
ax1.set_xlabel('Temperature (°C)', fontsize=8)
ax1.set_ylabel('Weight (%)', fontsize=8, color='black')
ax1.tick_params(axis='y', labelcolor='black', labelsize=8)
ax1.tick_params(axis='x', labelsize=8)

# DTG 곡선 (우측 Y축): 회색 점선 또는 다른 선 스타일로 구분 (흑백이므로 색상보다 선 스타일로 구분 권장)
ax2 = ax1.twinx()
ax2.plot(temperature, deriv_weight, color='gray', linestyle='--', linewidth=1.2, label='DTG')
ax2.set_ylabel('Deriv. Weight (%/°C)', fontsize=8, color='gray')
ax2.tick_params(axis='y', labelcolor='gray', labelsize=8)

# 축 범위 설정 (데이터에 맞춰 자동 조정하되, 필요시 수동 조정 가능)
ax1.set_xlim(temperature.min(), temperature.max())

# 범례 추가 (작게)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=7, frameon=False)

# 레이아웃 조정
plt.tight_layout()

# 파일 저장
output_path = os.path.join(OUT_DIR, "tga_annealed_bw.png")
plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
plt.close(fig)

print(f"그래프가 저장되었습니다: {output_path}")
