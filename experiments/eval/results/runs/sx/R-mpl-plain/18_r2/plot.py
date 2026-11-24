import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/18_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Excel 파일 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # 파랑, 주황, 초록

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 컬럼 이름 정리 (공백 제거 등)
    df.columns = [col.strip() for col in df.columns]
    
    # 데이터 추출
    temp = df['Temperature']
    weight = df['Weight(%)']
    dtg = df['D.W(%/C)']
    
    # 라벨명 간결하게 만들기 (예: "1006R1-V normal" -> "normal")
    label = sheet_name.split('-')[-1].strip()
    
    color = colors[i % len(colors)]
    
    # TGA 곡선 (왼쪽 y축)
    line1, = ax1.plot(temp, weight, color=color, linewidth=2, label=f'{label} TGA')
    
    # DTG 곡선 (오른쪽 y축)
    ax2 = ax1.twinx()
    line2, = ax2.plot(temp, dtg, color=color, linestyle='--', linewidth=1.5, alpha=0.7, label=f'{label} DTG')

# 축 설정
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax2.set_ylabel('Derivative Weight (%/°C)', fontsize=12)

# x축 틱 간격 100으로 설정
import numpy as np
max_temp = 900 # 데이터 최대 온도 고려하여 고정 또는 계산 가능하지만 요청에 따라 100 단위
ticks_x = np.arange(0, max_temp + 100, 100)
ax1.set_xticks(ticks_x)
ax1.set_xlim(0, max_temp)

# y2축(DTG) 범위 -0.05 ~ 1.2 로 설정 (요청 사항 반영)
# 참고: 데이터의 min값이 음수(-1.027 등)가 있는데, 요청 범위가 -0.05부터라면 
# 주로 양수 영역이나 작은 음수 영역을 강조하려는 의도로 보입니다. 
# 하지만 실제 데이터가 -1까지 내려가므로 -0.05로 제한하면 아래 부분이 잘릴 수 있습니다.
# 사용자의 명시적 요청 "-0.05~1.2"를 따릅니다.
ax2.set_ylim(-0.05, 1.2)

# y1축(TGA) 범위 자동 조정 (0~100 정도가 적절할 것으로 예상되나 자동화)
ax1.set_ylim(0, 105)

# 제목 및 범례
plt.title('TGA and DTG Curves Comparison', fontsize=14)

# 두 축의 라인 객체를 모두 포함하여 범례 생성
lines_labels = ax1.get_legend_handles_labels()
lines_labels2 = ax2.get_legend_handles_labels()
all_lines = lines_labels[0] + lines_labels2[0]
all_labels = lines_labels[1] + lines_labels2[1]

ax1.legend(all_lines, all_labels, loc='upper right', bbox_to_anchor=(1.1, 1), frameon=True)

plt.tight_layout()

# 출력 파일 저장
output_path = os.path.join(OUT_DIR, 'tga_plot.png')
os.makedirs(OUT_DIR, exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
