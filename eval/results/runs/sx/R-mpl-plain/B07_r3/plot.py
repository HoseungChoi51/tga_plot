import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B07_r3/out"

# 한국어 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 두 번째 시트(PVC) 읽기
df = pd.read_excel(DATA_FILE, sheet_name='PVC')

# 열 이름 확인 및 추출
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
deriv_col = 'Deriv. Weight (%/°C)'

x = df[temp_col]
y1 = df[weight_col]
y2 = df[deriv_col]

# 300 °C와 600 °C에서의 무게 값 찾기 (가장 가까운 온도점 사용)
idx_300 = (x - 300).abs().idxmin()
idx_600 = (x - 600).abs().idxmin()

w_300 = y1.iloc[idx_300]
t_300 = x.iloc[idx_300]
w_600 = y1.iloc[idx_600]
t_600 = x.iloc[idx_600]

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# TGA 곡선 (무게 %)
color1 = 'tab:blue'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
line1, = ax1.plot(x, y1, color=color1, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (미분 무게) - 두 번째 y축
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
line2, = ax2.plot(x, y2, color=color2, linestyle='--', label='미분 무게 (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# 300 °C와 600 °C에서의 무게 표시
ax1.scatter([t_300, t_600], [w_300, w_600], color='green', zorder=5, s=80, marker='o')
ax1.annotate(f'{t_300:.0f} °C\n{w_300:.1f} %', xy=(t_300, w_300),
             xytext=(t_300 + 20, w_300 + 5),
             arrowprops=dict(arrowstyle='->', color='green'),
             fontsize=10, color='green')
ax1.annotate(f'{t_600:.0f} °C\n{w_600:.1f} %', xy=(t_600, w_600),
             xytext=(t_600 + 20, w_600 + 5),
             arrowprops=dict(arrowstyle='->', color='green'),
             fontsize=10, color='green')

# 제목 및 범례
ax1.set_title('PVC TGA/DTG 분석 결과', fontsize=14)
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

plt.tight_layout()

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 그림 저장
output_path = os.path.join(OUT_DIR, 'pvc_tga.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
