import pandas as pd
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/17_r2/out"
FIG_WIDTH = 8
FIG_HEIGHT = 5
DPI = 600

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 출력 디렉토리 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 데이터 읽기
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# 색상 및 스타일 정의
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
labels = []

fig, ax1 = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
ax2 = ax1.twinx()

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # 열 이름 정리 (공백 제거 등)
    df.columns = [str(c).strip() for c in df.columns]
    
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dw_col = 'D.W(%/C)'
    
    # 데이터가 존재하는지 확인하고 플롯
    if temp_col in df.columns and weight_col in df.columns:
        color = colors[i % len(colors)]
        
        # TGA (Weight %) - 왼쪽 축
        line1, = ax1.plot(df[temp_col], df[weight_col], 
                          label=f'{sheet_name} (TGA)', 
                          color=color, linewidth=1.5)
        
        # DTG (D.W) - 오른쪽 축
        if dw_col in df.columns:
            line2, = ax2.plot(df[temp_col], df[dw_col], 
                              label=f'{sheet_name} (DTG)', 
                              color=color, linestyle='--', linewidth=1.5, alpha=0.7)
        
        labels.append((line1, line2))

# 축 레이블 및 제목
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax2.set_ylabel('Derivative Weight (%/°C)', fontsize=12)

ax1.set_title('TGA/DTG Analysis Comparison', fontsize=14)

# 범례 구성
lines1 = [l[0] for l in labels]
lines2 = [l[1] for l in labels]
labels1 = [l.get_label() for l in lines1]
labels2 = [l.get_label() for l in lines2]

ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9)

# 그리드
ax1.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_comparison.png")
plt.savefig(output_path, dpi=DPI)
plt.close()
