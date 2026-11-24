import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/22_r1/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (모든 시트를 읽음)
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # 기본 색상 팔레트에서 선택

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # 컬럼 이름이 공백이나 특수문자를 포함할 수 있으므로 strip 처리 권장되지만, 여기서는 주어진 그대로 사용
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dtg_col]
    
    # TGA 곡선 (Left Y-axis)
    color1 = colors[i % len(colors)]
    line1, = ax1.plot(x, y1, color=color1, label=f'{sheet_name} - Weight')
    
    # DTG 곡선 (Right Y-axis)
    # 요청사항: y2 선 색깔 초록으로, y2축 라벨 글자 색깔도 초록
    # 모든 샘플의 DTG를 같은 초록색 계열로 하되, 구분하기 위해 스타일 변경 또는 동일한 색 사용 가능
    # 보통 여러 샘플이면 색을 구분해야 하지만, 요청은 "y2 선 색깔 초록" 이므로 일관성 있게 초록색 계통으로 가되
    # 구분을 위해 알파값 조절이나 점선 등을 쓸 수 있음. 여기서는 명확한 초록색(#2ca02c)을 사용하되, 
    # 만약 여러 개가 겹쳐서 안 보이면 스타일을 달리함.
    
    ax2 = ax1.twinx()
    color2 = '#2ca02c' # Green
    
    # 각 샘플별로 약간 다른 녹색 톤이나 스타일로 구분 시도 (선택 사항이나, 요청은 단순히 '초록'이므로 메인 초록 사용)
    # 다만, 여러 시리즈가 있을 때 모두 같은 색이면 혼란스러울 수 있어, 
    # 첫 번째는 실선, 나머지는 점선 등으로 구분하거나, 명도를 다르게 할 수 있음.
    # 여기서는 요청대로 "초록색"을 유지하되, 시각적 구분을 위해 라인 스타일을 조금씩 변형하거나
    # 그냥 모두 진한 초록색으로 통일하고 레전드를 통해 구분하도록 함.
    
    if i == 0:
        linestyle = '-'
    elif i == 1:
        linestyle = '--'
    else:
        linestyle = ':'
        
    line2, = ax2.plot(x, y2, color=color2, linestyle=linestyle, alpha=0.8, label=f'{sheet_name} - DTG')

# 축 라벨 설정
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12, color=ax1.get_lines()[0].get_color()) # 첫 번째 TGA 색과 매칭하거나 검정색 유지 가능. 일반적으로 축 라벨은 해당 축 데이터와 같은 색인 경우가 많으나, 여러개면 검정색도 무방. 여기서는 검정색 기본 유지하거나 첫번째 색 사용. 표준적으로는 검정색.
ax1.set_ylabel('Weight (%)', fontsize=12, color='black') 

# 요청사항 반영: y2축 라벨 글자 색깔도 초록
ax2.set_ylabel('DTG (%/°C)', fontsize=12, color='#2ca02c')

# 축 눈금 라벨 색상도 일치시키는 것이 일반적임
ax2.tick_params(axis='y', labelcolor='#2ca02c')

# 제목 설정
plt.title('TGA and DTG Curves Comparison', fontsize=14)

# 레전드 추가
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9)

# 그리드 설정
ax1.grid(True, linestyle='--', alpha=0.5)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, 'tga_plot.png')
plt.savefig(output_path, dpi=300)
plt.close()
