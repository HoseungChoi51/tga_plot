import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/20_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Excel 파일 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # 각 샘플별 색상

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 열 이름이 공백이나 특수문자일 수 있으므로 strip 처리 및 기본 확인
    # 미리보기 기준: B=Temperature, C=Weight(%), D=D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dw_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns:
        continue
        
    x = df[temp_col]
    y_weight = df[weight_col]
    y_dw = df[dw_col]
    
    # TGA (Weight %) - 왼쪽 Y축
    color = colors[i % len(colors)]
    line1, = ax1.plot(x, y_weight, label=f'{sheet_name} Weight (%)', color=color, linewidth=2)
    
    # DTG (D.W %/C) - 오른쪽 Y축
    ax2 = ax1.twinx()
    line2, = ax2.plot(x, y_dw, linestyle='--', color=color, alpha=0.7, label=f'{sheet_name} DTG (%/C)')
    
    # 축 레이블은 첫 번째 반복에서만 설정하거나 공유되도록 관리
    if i == 0:
        ax1.set_ylabel('Weight (%)', fontsize=12)
        ax2.set_ylabel('DTG (%/C)', fontsize=12)

ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_title('TGA and DTG Curves for Different Samples', fontsize=14)

# 300~450 °C 구간 연한 회색으로 칠하기
ax1.axvspan(300, 450, color='gray', alpha=0.2, label='300-450 °C Region')

# 범례 추가
lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
lines = lines_labels[0][0] + lines_labels[1][0]
labels = lines_labels[0][1] + lines_labels[1][1]
ax1.legend(lines, labels, loc='upper right', fontsize=9)

# 그리드
ax1.grid(True, linestyle=':', alpha=0.6)

# 레이아웃 조정
plt.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
