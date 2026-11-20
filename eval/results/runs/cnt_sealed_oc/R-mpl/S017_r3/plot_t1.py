import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

FILE_PATH = "data/tga_batches.xlsx"
SHEET_NAME = "R2-260616-1"

# Read the specific sheet
df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)

# Ensure column names match the preview description (A 시간, B 온도, C 중량, D 미분중량)
# The headers might be in Korean as shown in preview
col_time = '시간 (min)'
col_temp = '온도 (°C)'
col_weight = '중량 (%)'
col_dtg = '미분중량 (%/°C)'

# Check if columns exist, otherwise try to access by position if header parsing failed slightly
if col_temp not in df.columns:
    # Fallback: assume standard order A, B, C, D -> Time, Temp, Weight, DTG
    cols = df.columns.tolist()
    col_temp = cols[1]
    col_weight = cols[2]
    col_dtg = cols[3]

temp = df[col_temp].values
weight = df[col_weight].values
dtg = df[col_dtg].values

# --- Calculation of Extrapolated Onset Temperature ---

# 1. Define the search range for DTG maximum: 450–800 °C
mask_range = (temp >= 450) & (temp <= 800)
temp_range = temp[mask_range]
dtg_range = dtg[mask_range]

if len(temp_range) == 0:
    raise ValueError("No data points found in the 450-800 °C range.")

# Find the index of the maximum absolute DTG value within this range
# Note: DTG is usually negative for mass loss, so we look for min value (most negative) 
# or max abs value. The preview shows positive values for DTG? 
# Wait, preview says: D 미분중량 (%/°C) [수치 -0.0134~2.07561]. 
# Usually TGA derivative is negative during decomposition. 
# Let's check the sign convention. If it represents weight loss rate, it might be plotted as positive magnitude or negative derivative.
# Standard TG curve: Weight decreases. dW/dT is negative.
# However, some instruments plot -dW/dT to make peaks positive.
# The prompt asks for "extrapolated onset". This is typically defined on the steepest slope of the mass loss step.
# If DTG is negative, the "maximum" drop is the minimum value.
# If DTG is plotted as positive magnitude of loss, the "maximum" is the peak.
# Let's assume standard scientific definition: find the point of inflection where slope is steepest.
# We will use the absolute value of the derivative to find the steepest part if signs are mixed, 
# but strictly speaking, for mass loss, we want the most negative slope if it's dW/dT.
# Given the range includes positive numbers up to ~2, and negative near 0, it looks like raw dW/dT.
# So the "peak" of degradation corresponds to the MINIMUM value of dW/dT (largest negative number).

idx_min_dtg_in_range = np.argmin(dtg_range)
temp_at_max_rate = temp_range[idx_min_dtg_in_range]
dtg_at_max_rate = dtg_range[idx_min_dtg_in_range]

# Get global indices for slicing
global_indices = np.where(mask_range)[0]
local_idx = idx_min_dtg_in_range
global_idx = global_indices[local_idx]

# 2. Calculate the Tangent Line at the steepest drop (max rate point)
# We need the slope (m) and intercept (b) of the tangent line y = m*x + b
# To get a robust slope, we can fit a linear regression on a small window around the peak point.
window_size = 10 # points on each side
start_idx = max(0, global_idx - window_size)
end_idx = min(len(temp), global_idx + window_size + 1)

t_window = temp[start_idx:end_idx]
w_window = weight[start_idx:end_idx]

# Fit linear model: Weight = Slope * Temp + Intercept
coeffs = np.polyfit(t_window, w_window, 1)
slope = coeffs[0]
intercept_tangent = coeffs[1]

# 3. Define the Baseline
# Prompt: "기준선은 500 °C 중량의 수평선으로 잡아 주세요."
# Find weight at approx 500 °C
idx_500 = np.argmin(np.abs(temp - 500))
baseline_weight = weight[idx_500]

# Baseline equation: y = baseline_weight (horizontal line)

# 4. Calculate Intersection (Extrapolated Onset)
# Tangent: W = slope * T + intercept_tangent
# Baseline: W = baseline_weight
# slope * T_onset + intercept_tangent = baseline_weight
# T_onset = (baseline_weight - intercept_tangent) / slope

if slope == 0:
    onset_temp = np.nan
else:
    onset_temp = (baseline_weight - intercept_tangent) / slope

# --- Plotting ---

fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot TG Curve (Weight %)
color = 'tab:blue'
ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color=color)
ax1.plot(temp, weight, color=color, label='TG 곡선')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.5)

# Create twin axis for DTG
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('미분중량 (%/°C)', color=color)
ax2.plot(temp, dtg, color=color, linestyle=':', label='DTG 곡선')
ax2.tick_params(axis='y', labelcolor=color)

# Plot Baseline (Horizontal line at 500C weight)
ax1.axhline(y=baseline_weight, color='gray', linestyle='-', linewidth=1, label=f'기준선 ({baseline_weight:.2f}%)')

# Plot Tangent Line
# Extend tangent line visually from slightly before onset to slightly after
tangent_t_start = onset_temp - 50
tangent_t_end = onset_temp + 100
# Restrict to data range for drawing safety
tangent_t_draw = np.linspace(max(temp.min(), tangent_t_start), min(temp.max(), tangent_t_end), 100)
tangent_w_draw = slope * tangent_t_draw + intercept_tangent

ax1.plot(tangent_t_draw, tangent_w_draw, color='green', linestyle='--', linewidth=1.5, label='접선 (최대 기울기)')

# Mark the Onset Point
ax1.scatter([onset_temp], [baseline_weight], color='black', s=50, zorder=5, marker='o')

# Add Text Annotation
text_str = f'Extrapolated Onset\n{onset_temp:.1f} °C'
ax1.annotate(text_str, 
             xy=(onset_temp, baseline_weight), 
             xytext=(onset_temp + 20, baseline_weight + 10),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=12, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=1, alpha=0.8))

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', framealpha=0.9)

plt.title(f'TGA Analysis: {SHEET_NAME}')
plt.tight_layout()

# Save
save_path = os.path.join(OUT_DIR, f"TGA_{SHEET_NAME}_Onset.png")
plt.savefig(save_path, dpi=300)
plt.close()
