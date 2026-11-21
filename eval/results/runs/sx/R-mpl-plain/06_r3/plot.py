import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/06_r3/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# Excel 파일 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 각 시트별로 TGA 데이터 추출 및 플롯 그리기
fig, axes = plt.subplots(len(sheet_names), 1, figsize=(8, 4 * len(sheet_names)), sharex=True)

# 만약 시트가 하나라면 axes가 array가 아니므로 리스트로 변환
if len(sheet_names) == 1:
    axes = [axes]

for idx, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # 컬럼 이름 확인 (데이터 미리보기 기준)
    # B: Temperature, C: Weight(%), D: D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    # 데이터 준비
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dtg_col]
    
    ax = axes[idx]
    
    # TGA 곡선 (Weight %) - 왼쪽 Y축
    line1, = ax.plot(x, y1, color='blue', label='TGA')
    ax.set_ylabel('Weight (%)', color='blue')
    ax.tick_params(axis='y', labelcolor='blue')
    
    # DTG 곡선 (D.W %/C) - 오른쪽 Y축
    ax2 = ax.twinx()
    line2, = ax2.plot(x, y2, color='red', linestyle='--', label='DTG')
    ax2.set_ylabel('DTG (%/°C)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    # X축 라벨은 마지막 서브플롯에만 표시하거나 모두 표시하되 공유하므로 마지막만 강조 가능
    # 여기서는 각 서브플롯마다 제목으로 구분
    ax.set_title(f'Sample: {sheet_name}')
    
    # 격자 켜기 (요청 사항)
    ax.grid(True, which='both', linestyle=':', linewidth=0.5, alpha=0.7)
    
    # 범례 제거 (요청 사항)
    # 이미 plot에 label을 넣었지만 legend 호출하지 않으면 안 나옴. 
    # 단, twin axis인 경우 주의 필요. 명시적으로 legend를 부르지 않음.

# 전체 X축 레이블
axes[-1].set_xlabel('Temperature (°C)')

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
