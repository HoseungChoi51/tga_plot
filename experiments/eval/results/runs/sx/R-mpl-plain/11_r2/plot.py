import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/11_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def plot_tga():
    # Excel 파일 읽기 (모든 시트)
    xls = pd.ExcelFile(DATA_FILE)
    sheet_names = xls.sheet_names
    
    if not sheet_names:
        return

    fig, axes = plt.subplots(len(sheet_names), 1, figsize=(8, 4 * len(sheet_names)), sharex=True)
    
    # 단일 시트인 경우 axes를 리스트로 변환하여 처리 통일
    if len(sheet_names) == 1:
        axes = [axes]

    for ax, sheet_name in zip(axes, sheet_names):
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        
        # 컬럼 이름 정리 (공백 제거 등)
        df.columns = df.columns.str.strip()
        
        # TGA 데이터 추출 (Temperature, Weight(%), D.W(%/C))
        try:
            temp_col = next(c for c in df.columns if 'temperature' in c.lower())
            weight_col = next(c for c in df.columns if 'weight' in c.lower())
            dw_col = next(c for c in df.columns if 'd.w' in c.lower() or 'dw' in c.lower())
        except StopIteration:
            continue
            
        x = df[temp_col]
        y1 = df[weight_col]
        y2 = df[dw_col]
        
        # TGA 곡선 (Weight %) - 왼쪽 Y축
        line1 = ax.plot(x, y1, label='Weight (%)', color='blue')
        ax.set_ylabel('Weight (%)', color='blue')
        ax.tick_params(axis='y', labelcolor='blue')
        
        # DTG 곡선 (D.W %/C) - 오른쪽 Y축
        ax2 = ax.twinx()
        line2 = ax2.plot(x, y2, label='DTG (%/°C)', color='red')
        ax2.set_ylabel('DTG (%/°C)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # 제목 설정
        ax.set_title(f'TGA/DTG Curve: {sheet_name}', fontsize=10)
        
        # 범례 추가
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper right', fontsize=8)
        
        # 그리드 표시
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # X축 레이블은 마지막 플롯에만 표시하거나 모든 플롯에 표시하되 간격 조절
        if ax == axes[-1]:
            ax.set_xlabel('Temperature (°C)')

    plt.tight_layout()
    
    # 출력 파일명 생성
    output_filename = os.path.join(OUT_DIR, "TGA_plot.png")
    
    # 그림 저장
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close(fig)

if __name__ == "__main__":
    # 출력 디렉토리가 없으면 생성
    os.makedirs(OUT_DIR, exist_ok=True)
    plot_tga()
