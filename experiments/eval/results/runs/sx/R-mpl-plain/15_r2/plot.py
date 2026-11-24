import pandas as pd
import matplotlib.pyplot as plt
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/15_r2/out"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # 데이터 읽기 (모든 시트)
    xls = pd.ExcelFile(DATA_FILE)
    sheet_names = xls.sheet_names
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, sheet_name in enumerate(sheet_names):
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # 컬럼 이름 정리 (공백 제거 등)
        df.columns = [col.strip() for col in df.columns]
        
        # TGA 데이터 추출
        # x: Temperature, y1: Weight(%), y2: D.W(%/C)
        if 'Temperature' not in df.columns or 'Weight(%)' not in df.columns or 'D.W(%/C)' not in df.columns:
            continue
            
        temp = df['Temperature']
        weight = df['Weight(%)']
        dw = df['D.W(%/C)']
        
        color = colors[i % len(colors)]
        
        # 주축(ax1): Weight (%)
        line1 = ax1.plot(temp, weight, label=f'{sheet_name} - Weight', color=color, linestyle='-')
        
        # 보조축(ax2): DTG (%/C)
        ax2 = ax1.twinx()
        line2 = ax2.plot(temp, dw, label=f'{sheet_name} - DTG', color=color, linestyle='--')
        
        # 레이블 추가를 위해 핸들 모으기
        if i == 0:
            lines_1 = line1
            lines_2 = line2
        else:
            lines_1 += line1
            lines_2 += line2

    # 축 라벨 설정
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', fontsize=12)
    ax2.set_ylabel('DTG (%/°C)', fontsize=12)
    
    # 제목
    plt.title('TGA and DTG Curves Comparison', fontsize=14)
    
    # 레이블 합치기
    labels_1 = [l.get_label() for l in lines_1]
    labels_2 = [l.get_label() for l in lines_2]
    
    # 모든 선을 하나의 레전드로 표시하되, 구분하기 쉽게 구성
    # Twin axes의 경우 레전드 처리가 복잡할 수 있으므로, 각각의 축에 맞는 레전드를 만들거나 통합함
    # 여기서는 가독성을 위해 Weight와 DTG를 모두 포함하는 통합 레전드를 생성
    
    all_lines = lines_1 + lines_2
    all_labels = labels_1 + labels_2
    
    ax1.legend(all_lines, all_labels, loc='center left', bbox_to_anchor=(1.1, 0.5), fontsize=9)
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 출력 파일명
    out_file = os.path.join(OUT_DIR, "tga_all_sheets.png")
    
    # 저장
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close(fig)

if __name__ == "__main__":
    main()
