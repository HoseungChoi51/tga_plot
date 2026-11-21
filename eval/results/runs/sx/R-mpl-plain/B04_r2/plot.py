import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

# Load data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B04_r2/out"

df = pd.read_csv(DATA_FILE)

# Extract columns
x = df.iloc[:, 0].values  # 2Theta (deg)
y = df.iloc[:, 1].values  # Intensity (counts)

# Find peaks using scipy.signal.find_peaks
peaks, properties = find_peaks(y, distance=50, prominence=50)

# Sort peaks by intensity in descending order to get the top 5 strongest peaks
if len(peaks) > 0:
    peak_intensities = y[peaks]
    sorted_indices = np.argsort(peak_intensities)[::-1]
    top_5_peak_indices = peaks[sorted_indices[:5]]
    top_5_peak_positions = x[top_5_peak_indices]
else:
    top_5_peak_positions = []

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, color='black', linewidth=1.2)

# Annotate top 5 peaks
for i, pos in enumerate(top_5_peak_positions):
    idx = np.argmin(np.abs(x - pos))
    ax.annotate(f'{pos:.2f}°', 
                xy=(x[idx], y[idx]), 
                xytext=(0, 10), 
                textcoords='offset points',
                ha='center', 
                va='bottom',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

# Labels and title
ax.set_xlabel('2θ (deg)', fontsize=12)
ax.set_ylabel('Intensity (counts)', fontsize=12)
ax.set_title('XRD 패턴', fontsize=14)

# Remove right spine and ticks
ax.spines['right'].set_visible(False)
ax.yaxis.tick_left()

plt.tight_layout()

# Save figure
output_path = f"{OUT_DIR}/xrd_pattern.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
