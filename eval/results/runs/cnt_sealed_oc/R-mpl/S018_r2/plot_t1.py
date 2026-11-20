import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# 설정
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# 파일 경로 및 시트 이름
file_path = "data/tga_batches.xlsx"
sheet1_name = 'R1-260326-1'
sheet2_name = 'R1-260716-1'

def get_weight_at_temp(df, temp_target):
    """
    주어진 온도(temp_target)에서의 중량을 선형 보간으로 찾아 반환합니다.
    데이터의 컬럼명이 정확히 일치하지 않거나 공백이 있을 수 있어 유연하게 처리하기보다는,
    미리보기에 나온 정확한 컬럼명을 사용한다고 가정합니다.
    """
    # 컬럼명 추출 (미리보기 기준: 'B 온도 (°C)', 'C 중량 (%)')
    col_temp = 'B 온도 (°C)'
    col_weight = 'C 중량 (%)'
    
    if col_temp not in df.columns or col_weight not in df.columns:
        # 만약 헤더 줄(단위 포함 등) 때문에 컬럼명이 다르면, 첫 번째와 세 번째 숫자열을 쓰는 방식 등 대안 가능
        # 하지만 문제 지시사항상 'read Korean headers as they are' 이므로 그대로 사용
        raise ValueError(f"Columns '{col_temp}' or '{col_weight}' not found.")

    temps = df[col_temp].values
    weights = df[col_weight].values
    
    # TGA 데이터는 일반적으로 온도가 오름차순이지만, 안전을 위해 정렬된 인덱스 사용 고려
    # 다만 searchsorted는 정렬된 배열에서만 동작하므로 확인
    if not np.all(np.diff(temps) >= 0):
        sort_idx = np.argsort(temps)
        temps = temps[sort_idx]
        weights = weights[sort_idx]

    # 범위 밖 처리
    if temp_target <= temps[0]:
        return weights[0]
    elif temp_target >= temps[-1]:
        return weights[-1]
    
    # 선형 보간
    idx = np.searchsorted(temps, temp_target)
    t0, t1 = temps[idx-1], temps[idx]
    w0, w1 = weights[idx-1], weights[idx]
    
    if t1 == t0:
        return w0
        
    ratio = (temp_target - t0) / (t1 - t0)
    return w0 + ratio * (w1 - w0)

try:
    # 데이터 읽기
    # openpyxl 엔진 명시적 지정하여 호환성 확보
    df1 = pd.read_excel(file_path, sheet_name=sheet1_name, engine='openpyxl')
    df2 = pd.read_excel(file_path, sheet_name=sheet2_name, engine='openpyxl')

    # 각 배치의 200°C와 450°C에서의 질량(W) 계산
    w200_1 = get_weight_at_temp(df1, 200.0)
    w450_1 = get_weight_at_temp(df1, 450.0)
    delta_w1 = w200_1 - w450_1

    w200_2 = get_weight_at_temp(df2, 200.0)
    w450_2 = get_weight_at_temp(df2, 450.0)
    delta_w2 = w200_2 - w450_2

    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 6))

    label1 = f'{sheet1_name} (ΔW 200-450°C: {delta_w1:.2f} wt%)'
    label2 = f'{sheet2_name} (ΔW 200-450°C: {delta_w2:.2f} wt%)'

    # 플롯 작성
    # x축: 온도, y축: 중량
    ax.plot(df1['B 온도 (°C)'], df1['C 중량 (%)'], label=label1, color='blue', linewidth=1.5)
    ax.plot(df2['B 온도 (°C)'], df2['C 중량 (%)'], label=label2, color='red', linestyle='--', linewidth=1.5)

    ax.set_xlabel('온도 (°C)', fontsize=12)
    ax.set_ylabel('중량 (%)', fontsize=12)
    ax.set_title('TG 곡선 비교: R1 배치들', fontsize=14)
    ax.legend(loc='upper right', frameon=True)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    # 축 범위 설정 (가독성을 위해 데이터 범위에 맞춤)
    min_t = min(df1['B 온도 (°C)'].min(), df2['B 온도 (°C)'].min())
    max_t = max(df1['B 온도 (°C)'].max(), df2['B 온도 (°C)'].max())
    ax.set_xlim(min_t, max_t)

    # 저장
    output_file = os.path.join(OUT_DIR, 'tg_comparison_R1.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Success: Saved figure to {output_file}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error occurred: {e}")
