import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B22_r1/out"
SHEET_NAME = "Raw"

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def main():
    # 1. 데이터 읽기
    try:
        df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # 컬럼명 확인 및 정리 (공백 제거 등)
    df.columns = [col.strip() for col in df.columns]
    
    # 필요한 컬럼 추출
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    
    if temp_col not in df.columns or weight_col not in df.columns:
        print("Required columns not found.")
        return

    temps = df[temp_col].values
    weights = df[weight_col].values
    
    # 2. 150 °C 기준점 찾기 및 정규화
    # 목표 온도: 150 °C
    target_temp = 150.0
    
    # 가장 가까운 데이터 포인트 인덱스 찾기
    idx_150 = np.argmin(np.abs(temps - target_temp))
    weight_at_150 = weights[idx_150]
    
    # 만약 150도 지점의 무게가 0에 가까우면 처리 불가 (여기서는 14~100% 사이이므로 안전)
    if weight_at_150 == 0:
        print("Weight at 150°C is zero, cannot normalize.")
        return
        
    # 정규화된 무게 계산: (현재 무게 / 150도 무게) * 100
    normalized_weights = (weights / weight_at_150) * 100.0
    
    # 3. 플롯 그리기
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # TGA 곡선 (정규화된 무게 vs 온도)
    ax.plot(temps, normalized_weights, color='blue', linewidth=1.5, label=f'{SHEET_NAME} (Normalized to 150°C)')
    
    # 150도 기준선 표시 (선택 사항이나 이해를 돕기 위해 dashed line 추가 가능하나, 요청은 곡선 자체임)
    # 여기서는 깔끔하게 곡선만 그리되, 축 레이블을 명확히 함
    
    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('Weight (%) (Relative to 150°C)', fontsize=12)
    ax.set_title(f'TGA Curve of {SHEET_NAME} Sample\n(Normalized: Weight at 150°C = 100%)', fontsize=14)
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='best')
    
    # 축 범위 조정 (데이터 범위에 맞춰 자동 조정되지만, 최소/최대값 확인용)
    ax.set_xlim(min(temps), max(temps))
    # y축은 정규화되었으므로 대략 0~110% 정도 예상되나 데이터에 따라 조절
    ax.set_ylim(0, max(normalized_weights)*1.1) 
    
    plt.tight_layout()
    
    # 4. 저장
    output_filename = f"{SHEET_NAME}_TGA_normalized_150C.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    # 디렉토리가 없으면 생성
    os.makedirs(OUT_DIR, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    main()
