import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B08_r2/out"

# 한국어 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # 1. 데이터 읽기 (Raw 시트)
    df_raw = pd.read_excel(DATA_FILE, sheet_name='Raw')
    
    # 컬럼명 정리 (공백 제거 등) - 미리보기 기준: "Temperature (°C)", "Weight (%)"
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    
    # 결측치 제거 및 정렬 (TGA 데이터 특성상 온도 순으로 정렬되어 있을 가능성이 높지만 안전을 위해)
    df_clean = df_raw[[temp_col, weight_col]].dropna()
    df_clean = df_clean.sort_values(by=temp_col)
    
    temps = df_clean[temp_col]
    weights = df_clean[weight_col]
    
    # 2. 그래프 그리기
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # TGA 곡선 plotting
    ax.plot(temps, weights, color='black', linewidth=1.5, label='Raw')
    
    # 무게 50% 위치에 가로 보조선 추가
    ax.axhline(y=50, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    
    # 축 라벨 및 제목
    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('Weight (%)', fontsize=12)
    ax.set_title('TGA Curve of Raw Sample', fontsize=14)
    
    # 오른쪽 위에 메모 텍스트 추가
    # loc='upper right' 사용 가능하지만, 위치 미세 조정을 위해 text 사용 권장
    # 상단 우측 여백에 배치
    ax.text(0.95, 0.95, '공기, 10 °C/min', 
            transform=ax.transAxes, 
            fontsize=11, 
            verticalalignment='top', 
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', alpha=0.8))
            
    # 격자 표시
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 3. 저장
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    output_path = os.path.join(OUT_DIR, "tga_raw_annotated.png")
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    main()
