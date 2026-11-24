import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# 데이터 읽기
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B04_r1/out"

df = pd.read_csv(DATA_FILE)

# 컬럼명 확인 및 추출
col_x = df.columns[0]  # "2Theta (deg)"
col_y = df.columns[1]  # "Intensity (counts)"

x = df[col_x].values
y = df[col_y].values

# 피크 찾기: 가장 강한 5개 피크
peaks, properties = find_peaks(y, height=np.max(y)*0.3, distance=10)

# 높이에 따라 정렬하여 상위 5개 선택
peak_heights = y[peaks]
top_indices = np.argsort(peak_heights)[::-1][:5]
top_peaks = peaks[top_indices]
top_2theta = x[top_peaks]
top_intensities = peak_heights[top_indices]

# 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
fig, ax1 = plt.subplots(figsize=(8, 6))

# XRD 패턴 그리기
ax1.plot(x, y, color='#1f4e9c', linewidth=1.2, label='XRD Pattern')

# 축 라벨
ax1.set_xlabel('2θ (degrees)', fontsize=12)
ax1.set_ylabel('Intensity (counts)', fontsize=12)

# 축 범위
ax1.set_xlim([10, 80])
ax1.set_ylim([0, np.max(y) * 1.1])

# 틱 간격
ax1.set_xticks(np.arange(10, 81, 10))
ax1.set_yticks(np.arange(0, np.max(y)+200, 200))

# 격자
ax1.grid(True, linestyle='--', alpha=0.5)

# 피크 표시
for i, (px, py) in enumerate(zip(top_2theta, top_intensities)):
    ax1.scatter(px, py, color='#c0392b', s=50, zorder=5)
    ax1.annotate(f'{px:.1f}°', xy=(px, py), xytext=(0, 10), textcoords='offset points',
                 ha='center', va='bottom', fontsize=9, color='#c0392b', fontweight='bold')

# 제목
ax1.set_title('XRD Pattern with Top 5 Peaks', fontsize=14)

# 범례
ax1.legend(loc='upper right', fontsize=10)

# 저장
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, 'xrd_pattern.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
