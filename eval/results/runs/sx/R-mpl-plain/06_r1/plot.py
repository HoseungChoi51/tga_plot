import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-plain/06_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Excel 파일 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 그래프 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # 각 시트별 색상 지정

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 컬럼명 확인 및 데이터 추출
    # 미리보기에 따르면 B: Temperature, C: Weight(%), D: D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dw_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns or dw_col not in df.columns:
        continue
        
    x = df[temp_col]
    y_weight = df[weight_col]
    y_dw = df[dw_col]
    
    # TGA 곡선 (Weight %) - 왼쪽 Y축
    color = colors[i % len(colors)]
    line1, = ax1.plot(x, y_weight, label=f'{sheet_name} Weight', color=color, linewidth=2)
    
    # DTG 곡선 (D.W %/C) - 오른쪽 Y축 (반전하여 보기 좋게 처리 가능하나, 원본 값 사용)
    ax2 = ax1.twinx()
    line2, = ax2.plot(x, y_dw, linestyle='--', color=color, alpha=0.7, linewidth=1.5)

# 축 레이블 설정
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12, color='black')
ax2.set_ylabel('DTG (%/°C)', fontsize=12, color='gray')

# 격자 켜기
ax1.grid(True, linestyle='--', alpha=0.6)

# 범례 제거 요청에 따라 legend 호출하지 않음
# ax1.legend() -> 생략

# 타이틀
plt.title('TGA Analysis Results', fontsize=14)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_plot.png")
os.makedirs(OUT_DIR, exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
