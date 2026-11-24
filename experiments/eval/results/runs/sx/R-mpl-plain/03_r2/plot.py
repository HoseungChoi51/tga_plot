import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# 파일 경로 및 출력 디렉토리 설정
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/03_r2/out"
os.makedirs(OUT_DIR, exist_ok=True)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 읽기 (시트 이름: "1006R1-V acid")
sheet_name = "1006R1-V acid"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# 열 이름 확인 및 변수 할당
# 예상된 열: Time, Temperature, Weight(%), D.W(%/C)
temp_col = 'Temperature'
weight_col = 'Weight(%)'
dtg_col = 'D.W(%/C)'

# x축 범위 필터링 (100~800)
mask = (df[temp_col] >= 100) & (df[temp_col] <= 800)
df_filtered = df[mask].copy()

# DTG 피크 찾기 (음수 값이므로 절댓값 기준으로 피크를 찾거나, 최소값을 찾음)
# find_peaks는 양수 피크를 찾으므로, -DTG 값을 사용하거나 height 파라미터로 음수 처리 가능
# 여기서는 -DTG 값을 사용하여 가장 큰 감소율(가장 깊은 골)을 피크로 인식
neg_dtg = -df_filtered[dtg_col].values

# distance를 설정하여 너무 가까운 피크들을 제외하고 주요 피크 2개만 찾기 위해 노력
# 일반적으로 TGA에서 주요 분해 단계는 명확히 구분되므로 distance를 충분히 크게 잡음
peaks, properties = find_peaks(neg_dtg, distance=50, prominence=0.1)

# 피크가 2개보다 많이 나오면 prominent한 순서대로 정렬 후 상위 2개 선택
if len(peaks) > 2:
    # prominence 기준 내림차순 정렬 인덱스
    sorted_indices = np.argsort(properties['prominences'])[::-1][:2]
    peaks = peaks[sorted_indices]
    
# 피크가 2개 미만이면 그냥 있는 대로 사용 (요청사항은 2개 표시지만 데이터에 따라 다를 수 있음)
peak_temps = df_filtered[temp_col].values[peaks]
peak_weights = df_filtered[weight_col].values[peaks]
peak_dtgs = df_filtered[dtg_col].values[peaks]

# 플롯 생성
fig, ax1 = plt.subplots(figsize=(10, 6))

# TGA 곡선 (Weight %) - 왼쪽 y축
ax1.plot(df_filtered[temp_col], df_filtered[weight_col], color='blue', label='TGA (Weight %)')
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xlim(100, 800)
ax1.grid(True, linestyle='--', alpha=0.5)

# DTG 곡선 (D.W %/C) - 오른쪽 y축
ax2 = ax1.twinx()
ax2.plot(df_filtered[temp_col], df_filtered[dtg_col], color='red', label='DTG (Rate of Weight Loss)')
ax2.set_ylabel('무게 변화율 (%/°C)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# 피크 표시
for i, (pt, pw, pdt) in enumerate(zip(peak_temps, peak_weights, peak_dtgs)):
    # TGA 곡선 위의 해당 온도 지점의 무게 위치 계산은 필요 없으므로, DTG 피크 위치나 텍스트로 표시하는 것이 일반적임
    # 보통 DTG 피크 점 자체를 마커로 찍고 라벨링함
    ax2.scatter(pt, pdt, color='black', zorder=5)
    # 라벨 배치: 피크 위치 근처에 텍스트 추가
    ax2.annotate(f'Peak {i+1}: {pt:.1f}°C', 
                 xy=(pt, pdt), 
                 xytext=(pt + 20, pdt - 0.2), # 오프셋 조정
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 fontsize=9, ha='left')

# 범례
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.title(f'TGA/DTG Analysis ({sheet_name})', fontsize=14)
plt.tight_layout()

# 저장
output_path = os.path.join(OUT_DIR, "tga_acid_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
