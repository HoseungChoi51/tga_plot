import pandas as pd
import matplotlib.pyplot as plt
import os

# 데이터 파일 경로와 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B24_r2/out"

# 한국어 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # PE 시트 읽기
    df = pd.read_excel(DATA_FILE, sheet_name='PE')
    
    # 온도 단위를 Celsius에서 Kelvin으로 변환 (K = °C + 273.15)
    df['Temperature (K)'] = df['Temperature (°C)'] + 273.15
    
    # 그래프 생성
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # TGA 곡선 (Weight %) - 왼쪽 y축
    color1 = 'tab:blue'
    ax1.set_xlabel('Temperature (K)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    line1 = ax1.plot(df['Temperature (K)'], df['Weight (%)'], color=color1, label='Weight (%)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # DTG 곡선 (Deriv. Weight %/°C) - 오른쪽 y축
    # 주의: Deriv. Weight는 원래 °C 기준이므로, K로 변경해도 기울기 값 자체는 동일함 (온도 차이는 같으므로)
    # 하지만 라벨은 명확성을 위해 유지하거나 조정 가능. 여기서는 원본 데이터를 그대로 사용하되 x축만 K로 변경.
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Deriv. Weight (%/°C)', color=color2, fontsize=12)
    line2 = ax2.plot(df['Temperature (K)'], df['Deriv. Weight (%/°C)'], color=color2, linestyle='--', label='Deriv. Weight (%/°C)')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # 제목 및 범례
    plt.title('TGA and DTG Curves for PE (Temperature in Kelvin)', fontsize=14)
    
    # 두 축의 선을 합쳐서 하나의 범례로 표시
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # 레이아웃 자동 조정
    fig.tight_layout()
    
    # 출력 파일명
    output_filename = "PE_TGA_Kelvin.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    # 저장
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Graph saved to {output_path}")

if __name__ == "__main__":
    main()
