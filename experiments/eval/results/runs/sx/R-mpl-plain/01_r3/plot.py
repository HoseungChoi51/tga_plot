import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/01_r3/out"

# 출력 디렉토리가 없으면 생성
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Excel 파일 읽기 (모든 시트)
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

# 그래프 그리기
fig, axes = plt.subplots(len(sheet_names), 1, figsize=(10, 4 * len(sheet_names)), sharex=True)

# 단일 시트인 경우 axes를 리스트로 변환
if len(sheet_names) == 1:
    axes = [axes]

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # 데이터 정제: 결측치 제거 및 숫자형으로 변환 시도
    df = df.dropna(subset=['Temperature', 'Weight(%)', 'D.W(%/C)'])
    df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
    df['Weight(%)'] = pd.to_numeric(df['Weight(%)'], errors='coerce')
    df['D.W(%/C)'] = pd.to_numeric(df['D.W(%/C)'], errors='coerce')
    df = df.dropna()
    
    ax1 = axes[i]
    
    # TGA 곡선 (Weight %) - 왼쪽 Y축
    color_tga = '#1f77b4'
    line1 = ax1.plot(df['Temperature'], df['Weight(%)'], label='Weight (%)', color=color_tga, linewidth=2)
    ax1.set_ylabel('Weight (%)', fontsize=12, color=color_tga)
    ax1.tick_params(axis='y', labelcolor=color_tga)
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # DTG 곡선 (D.W %/C) - 오른쪽 Y축
    ax2 = ax1.twinx()
    color_dtg = '#d62728'
    line2 = ax2.plot(df['Temperature'], df['D.W(%/C)'], label='DTG (%/°C)', color=color_dtg, linewidth=2, linestyle='--')
    ax2.set_ylabel('DTG (%/°C)', fontsize=12, color=color_dtg)
    ax2.tick_params(axis='y', labelcolor=color_dtg)
    
    # 제목 설정
    ax1.set_title(f'TGA Analysis: {sheet_name}', fontsize=14, fontweight='bold')
    
    # X축 라벨은 마지막 서브플롯에만 표시하거나 모두 표시하되 간격 조정
    if i == len(sheet_names) - 1:
        ax1.set_xlabel('Temperature (°C)', fontsize=12)
    
    # 범례 추가
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right')

plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "TGA_analysis.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
