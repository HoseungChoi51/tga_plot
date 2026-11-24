import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/19_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
# 전체 글자 색깔 회색, 글자 크기 13 설정
plt.rcParams['text.color'] = 'gray'
plt.rcParams['axes.labelcolor'] = 'gray'
plt.rcParams['xtick.color'] = 'gray'
plt.rcParams['ytick.color'] = 'gray'
plt.rcParams['font.size'] = 13

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# Excel 파일 읽기 (모든 시트)
xls = pd.ExcelFile(DATA_FILE)

fig, axes = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

sheet_names = xls.sheet_names

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 컬럼명 정리 (strip 공백 등)
    df.columns = [col.strip() for col in df.columns]
    
    # TGA 데이터 추출: Temperature (X), Weight% (Y1), D.W (Y2)
    # 일반적으로 TGA는 온도에 따른 무게 변화(TG)와 그 미분값(DTG)을 함께 보여줌
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        if 'Temperature' in col:
            temp_col = col
        elif 'Weight' in col or 'weight' in col:
            weight_col = col
        elif 'D.W' in col or 'DTG' in col or 'dW' in col.lower():
            dtg_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col]
    y_tg = df[weight_col]
    
    ax = axes[i]
    
    # TG 곡선 (무게 %)
    line1 = ax.plot(x, y_tg, label='TG (%)', color='black')
    ax.set_ylabel('Weight (%)')
    ax.tick_params(axis='y', labelleft=True)
    
    # DTG 곡선 (미분 무게 %) - 오른쪽 Y축 사용 권장이나, 여기서는 단순화를 위해 별도 축 없이 또는 공유 축에 표시
    # 보통 TGA 플롯은 TG와 DTG를 같은 그래프에 다른 스케일로 그리거나, 아래쪽 서브플롯으로 분리함.
    # 위 코드에서는 각 시트를 하나의 서브플롯으로 나누었으므로, 각 서브플롯 내에 TG와 DTG를 모두 표현하는 것이 일반적임.
    # 하지만 문제의 요청이 "전체 글자 색깔 회색, 글자 크기 13"이며 특정 레이아웃 지시가 없으므로, 
    # 가장 표준적인 방식인 각 샘플별로 TG와 DTG를 한 그래프에 이중 축으로 표시하거나, 
    # 여기서는 3개의 서브플롯이 이미 있으므로 각 서브플롯에 TG만 그리고 DTG는 생략하거나, 
    # 혹은 각 서브플롯에 TG와 DTG를 함께 그리되 스케일 차이를 고려해야 함.
    
    # 더 나은 가독성을 위해: 각 서브플롯에 TG(왼쪽축)와 DTG(오른쪽축)를 그림
    if dtg_col and dtg_col in df.columns:
        y_dtg = df[dtg_col]
        ax2 = ax.twinx()
        line2 = ax2.plot(x, y_dtg, label='DTG (%/°C)', color='red', linestyle='--')
        ax2.set_ylabel('DTG (%/°C)')
        ax2.tick_params(axis='y', labelright=True)
        
        # 범례 합치기
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='best')
    else:
        ax.legend(loc='best')
        
    ax.set_title(f'{sheet_name}')
    ax.grid(True, linestyle=':', alpha=0.6)

# X축 라벨은 마지막에만
axes[-1].set_xlabel('Temperature (°C)')

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tga_plot.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
