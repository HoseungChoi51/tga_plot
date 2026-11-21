import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# 설정
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B13_r2/out"
SHEET_NAME = "PVC"

# 폰트 설정 (한글 지원)
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 로드
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# 열 이름 확인 및 변수 할당
# 일반적으로 B열: Temperature, C열: Weight, D열: Deriv. Weight
# 데이터 미리보기에 따르면:
# col B: "Temperature (°C)"
# col C: "Weight (%)"
# col D: "Deriv. Weight (%/°C)"

temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

# 결측치 제거 및 정렬
df_clean = df[[temp_col, weight_col, dtg_col]].dropna()
df_clean = df_clean.sort_values(by=temp_col).reset_index(drop=True)

temps = df_clean[temp_col].values
weights = df_clean[weight_col].values
dtgs = df_clean[dtg_col].values

# DTG를 양수로 변환하여 피크 찾기 준비 (-DTG가 질량 감소 속도이므로 피크는 위로 향함)
neg_dtgs = -dtgs

# 피크 탐지: 무게가 확 꺾이는 곳은 DTG의 최대값(절대값 기준)이 되는 지점입니다.
# 150도 이상에서 가장 큰 두 개의 피크를 찾습니다.
min_temp = 150
mask = temps >= min_temp
filtered_temps = temps[mask]
filtered_neg_dtgs = neg_dtgs[mask]

# find_peaks 사용
# distance 파라미터로 너무 가까운 피크들을 방지하고, height로 최소 높이를 설정할 수 있지만
# 여기서는 단순히 가장 prominent 한 두 개를 찾기 위해 prominence나 height 필터링 없이
# 모든 피크를 찾고, 그 중 값이 큰 순서대로 정렬하는 방식을 사용합니다.
peaks_indices, properties = find_peaks(filtered_neg_dtgs, prominence=0.1) # 적절한 prominence 조정 필요할 수 있음

if len(peaks_indices) == 0:
    # 만약 prominence 때문에 못 찾으면 조건 완화
    peaks_indices, properties = find_peaks(filtered_neg_dtgs)

if len(peaks_indices) > 0:
    # 피크 높이(neg_dtgs 값) 기준으로 내림차순 정렬하여 상위 2개 선택
    peak_heights = filtered_neg_dtgs[peaks_indices]
    sorted_peak_order = np.argsort(peak_heights)[::-1]
    
    top_2_peak_indices_in_filtered = peaks_indices[sorted_peak_order[:2]]
    
    # 원본 인덱스로 변환
    top_2_peak_indices_original = []
    for idx in top_2_peak_indices_in_filtered:
        # filtered 배열에서의 인덱스를 원본 df_clean의 인덱스로 매핑
        # mask된 부분의 시작 인덱스를 찾아야 함
        original_idx = np.where(mask)[0][idx]
        top_2_peak_indices_original.append(original_idx)
        
    # 온도 및 값 추출
    peak_temps = [temps[i] for i in top_2_peak_indices_original]
    peak_weights = [weights[i] for i in top_2_peak_indices_original]
else:
    peak_temps = []
    peak_weights = []

# 플롯 생성
fig, ax1 = plt.subplots(figsize=(8, 6))

# Y1: Weight (%)
color1 = '#1f4e9c'
ax1.plot(temps, weights, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Y2: DTG (%/°C), 음수 부호 제거하여 위쪽으로 표시
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(temps, -dtgs, color=color2, linestyle='--', label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# 제목
ax1.set_title(f'TGA Plot: {SHEET_NAME}', fontsize=14)

# 피크 표시
for i, t_peak in enumerate(peak_temps):
    w_peak = weights[np.argmin(np.abs(temps - t_peak))] # 가장 가까운 실제 데이터 포인트
    
    # 마커 그리기
    ax1.plot(t_peak, w_peak, 'o', color='green', markersize=8, zorder=5)
    
    # 라벨 텍스트
    label_text = f'{t_peak:.1f} °C'
    # 위치 조정: 오른쪽 위에 표시
    ax1.annotate(label_text, 
                 xy=(t_peak, w_peak), 
                 xytext=(t_peak + 20, w_peak + 5),
                 fontsize=10,
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# 범례
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

# 격자
ax1.grid(True, linestyle=':', alpha=0.6)

# 레이아웃 조정
plt.tight_layout()

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, f"{SHEET_NAME}_peaks.png")
plt.savefig(output_path, dpi=300)
plt.close()
