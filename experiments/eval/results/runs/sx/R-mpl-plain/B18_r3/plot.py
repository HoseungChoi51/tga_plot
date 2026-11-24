import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B18_r3/out"
SHEET_NAME = "Annealed"

# 폰트 설정 (한글 지원)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

def calculate_onset_temperature(df, temp_col='Temperature (°C)', weight_col='Weight (%)', deriv_col='Deriv. Weight (%/°C)'):
    """
    TGA 데이터에서 외삽 개시 온도(Onset Temperature)를 계산합니다.
    방법: DTG 곡선의 최대 손실 속도 피크 지점에서 접선을 긋고, 
    초기 질량 안정 구간(Tg 이전 또는 분해 시작 전 베이스라인)과의 교차점을 찾습니다.
    여기서는 더 일반적인 방법인 DTG 피크의 좌측 변곡점 근처에서 접선을 이용하거나,
    단순히 DTG가 특정 임계값을 넘어서는 시점을 근사하는 대신,
    가장 정확한 방법 중 하나인 'Tang method'의 단순화된 버전이나,
    일반적으로 많이 쓰이는 'DTG peak tangent intersection with baseline' 방식을 사용합니다.
    
    단, 간단한 구현을 위해 다음과 같은 접근법을 사용하겠습니다:
    1. DTG 절대값이 최대인 지점(Peak Temp)을 찾음.
    2. Peak Temp 이전 구간에서 DTG가 급격히 떨어지는(음수 값이 커지는) 영역의 선형 회귀 직선과
       초기 베이스라인(거의 0에 가까운 구간)의 교차점을 Onset으로 추정합니다.
    """
    temps = df[temp_col].values
    weights = df[weight_col].values
    dtg = df[deriv_col].values
    
    # DTG가 음수인 구간만 고려 (질량 감소 구간)
    # 노이즈 제거를 위해 약간의 스무딩이 필요할 수 있으나, 주어진 데이터가 이미 미분된 상태라고 가정
    
    # 1. DTG 피크(최대 손실 속도, 즉 가장 큰 음수 값) 찾기
    min_dtg_idx = np.argmin(dtg)
    peak_temp = temps[min_dtg_idx]
    min_dtg_val = dtg[min_dtg_idx]
    
    # 2. Onset 계산: Tangent Method
    # 피크 지점에서의 접선을 구하기 위해 피크 주변 몇 포인트를 사용하여 선형 회귀 수행
    window_size = 5
    start_idx = max(0, min_dtg_idx - window_size)
    end_idx = min(len(temps), min_dtg_idx + window_size + 1)
    
    t_peak_window = temps[start_idx:end_idx]
    dtg_peak_window = dtg[start_idx:end_idx]
    
    # 피크 주변의 기울기(m)와 절편(b) 계산
    if len(t_peak_window) > 1:
        m, b = np.polyfit(t_peak_window, dtg_peak_window, 1)
        
        # 베이스라인 정의: 분해가 시작되기 전의 DTG 평균값 (초기 부분)
        # 보통 첫 10~20% 구간 또는 DTG가 0에 가까운 구간
        baseline_end_idx = int(len(temps) * 0.1) # 처음 10% 데이터를 베이스라인으로 간주
        if baseline_end_idx < 5: baseline_end_idx = 5
        
        baseline_dtg = np.mean(dtg[:baseline_end_idx])
        
        # 교차점 계산: y = mx + b 와 y = baseline_dtg 의 교차점 x
        # baseline_dtg = m * onset_temp + b
        # onset_temp = (baseline_dtg - b) / m
        
        if m != 0:
            onset_temp = (baseline_dtg - b) / m
            
            # 물리적으로 말이 되는지 확인: onset은 peak보다 낮아야 함
            if onset_temp >= peak_temp or onset_temp < temps[0]:
                # 만약 계산값이 이상하면, DTG가 특정 비율(예: 최소값의 10%)을 넘는 첫 지점으로 대체
                threshold = min_dtg_val * 0.1 # 10% of max loss rate
                idx_onset_approx = np.where(dtg <= threshold)[0][0]
                onset_temp = temps[idx_onset_approx]
        else:
             # m이 0인 경우 예외 처리
             threshold = min_dtg_val * 0.1
             idx_onset_approx = np.where(dtg <= threshold)[0][0]
             onset_temp = temps[idx_onset_approx]
    else:
        onset_temp = peak_temp # 데이터 부족 시 피크 온도를 반환

    return onset_temp, peak_temp, temps, weights, dtg

def main():
    # 출력 디렉토리 생성
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # 데이터 로드
    try:
        df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return

    # 열 이름 확인 및 정리
    cols = df.columns.tolist()
    temp_col = [c for c in cols if 'Temperature' in c][0]
    weight_col = [c for c in cols if 'Weight' in c and 'Deriv' not in c][0]
    deriv_col = [c for c in cols if 'Deriv' in c][0]
    
    # 결측치 처리
    df_clean = df[[temp_col, weight_col, deriv_col]].dropna()
    
    # Onset 온도 계산
    onset_temp, peak_temp, temps, weights, dtg = calculate_onset_temperature(df_clean, temp_col, weight_col, deriv_col)
    
    # 그래프 그리기
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # TGA 곡선 (Weight %)
    color_tga = 'tab:red'
    ax1.set_xlabel('온도 (°C)')
    ax1.set_ylabel('질량 (%)', color=color_tga)
    ax1.plot(temps, weights, color=color_tga, label='TGA (Weight %)', linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color_tga)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # DTG 곡선 (Deriv. Weight) - 두 번째 축
    ax2 = ax1.twinx()
    color_dtg = 'tab:blue'
    ax2.set_ylabel('미분 질량 (%/°C)', color=color_dtg)
    ax2.plot(temps, dtg, color=color_dtg, label='DTG (Deriv. Weight)', linewidth=1.5, alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color_dtg)
    
    # Onset 표시
    # Onset 점 표시
    # 해당 온도의 질량 값을 보간하여 얻음
    onset_weight = np.interp(onset_temp, temps, weights)
    ax1.axvline(x=onset_temp, color='green', linestyle=':', linewidth=2, label=f'Onset Temp: {onset_temp:.2f} °C')
    ax1.plot(onset_temp, onset_weight, 'go', markersize=8, zorder=5)
    
    # Peak Temp 표시 (참고용)
    peak_weight = np.interp(peak_temp, temps, weights)
    ax1.axvline(x=peak_temp, color='orange', linestyle='--', linewidth=1, label=f'Peak Temp: {peak_temp:.2f} °C')
    
    # 제목 및 범례
    ax1.set_title(f'TGA Analysis ({SHEET_NAME}) - Onset Temperature Estimation')
    
    # 범례 위치 조정 (두 축의 범례를 합침)
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')
    
    # 레이아웃 조정
    fig.tight_layout()
    
    # 저장
    output_path = os.path.join(OUT_DIR, 'tga_annealed_onset.png')
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    print(f"그래프가 저장되었습니다: {output_path}")
    print(f"추정된 외삽 개시 온도 (Onset Temperature): {onset_temp:.2f} °C")
    print(f"피크 온도 (Peak Temperature): {peak_temp:.2f} °C")

if __name__ == "__main__":
    main()
