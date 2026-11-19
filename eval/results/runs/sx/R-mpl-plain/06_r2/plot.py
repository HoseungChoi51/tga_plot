import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/06_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (모든 시트)
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 7))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # 기본 색상 팔레트 사용 또는 커스텀 가능

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xl, sheet_name=sheet_name)
    
    # 열 이름 확인 및 데이터 추출
    # TGA guess에 따라 B: Temperature, C: Weight(%), D: D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    x_data = df[temp_col]
    y_weight = df[weight_col]
    y_dtg = df[dtg_col]
    
    # TGA 곡선 (Left Y-axis)
    color_tga = colors[i % len(colors)]
    line1 = ax1.plot(x_data, y_weight, label=f'{sheet_name} - Weight', color=color_tga, linewidth=1.5)
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', fontsize=12, color=color_tga)
    ax1.tick_params(axis='y', labelcolor=color_tga)
    
    # DTG 곡선 (Right Y-axis)
    ax2 = ax1.twinx()
    color_dtg = colors[(i + 1) % len(colors)] # 다른 색으로 구분하거나 같은 계열 사용 가능
    # 여기서는 각 샘플별로 TGA와 DTG를 명확히 구분하기 위해 스타일 차이를 두거나, 
    # 요청사항이 "범례 없애고 격자 켜줘"이므로 시각적 혼란을 줄이기 위해 단순화합니다.
    # 보통 TGA는 실선, DTG는 점선 등으로 구분하지만, 범례가 없으므로 색상으로만 구분합니다.
    # 다만, 하나의 축에 여러 개가 겹치면 복잡하므로, 각 샘플의 TGA는 왼쪽, DTG는 오른쪽 축에 그립니다.
    # 모든 샘플의 TGA가 왼쪽, 모든 샘플의 DTG가 오른쪽이라면 색상 매칭이 중요합니다.
    
    # 다시 생각: 사용자가 "범례 없애고"라고 했으므로, 어떤 선이 무엇인지 알 수 없게 됩니다.
    # 하지만 일반적으로 TGA 플롯은 샘플별 비교를 위해 그려집니다.
    # 여기서는 각 샘플의 TGA(실선)와 DTG(점선)를 그리되, 범례는 제거합니다.
    # 색상 일관성을 위해 샘플별로 고유한 색상을 할당하고, TGA는 실선, DTG는 점선으로 구분합니다.
    
    line2 = ax2.plot(x_data, y_dtg, linestyle='--', label=f'{sheet_name} - dW/dT', color=color_tga, alpha=0.7, linewidth=1.5)

# 축 레이블 설정 (중복 방지를 위해 한 번만 설정)
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax2.set_ylabel('dW/dT (%/°C)', fontsize=12)

# 제목 설정
plt.title('TGA and DTG Analysis Results', fontsize=14)

# 격자 표시
ax1.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

# 범례 제거
# ax1.legend(loc='best') -> 호출하지 않음
# ax2.legend(loc='best') -> 호출하지 않음

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tga_plot.png')
plt.savefig(output_path, dpi=300)
plt.close()
