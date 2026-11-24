import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B09_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read only the PE sheet
df = pd.read_excel(DATA_FILE, sheet_name="PE")

# Extract columns based on data preview
# Col B: Temperature (°C), Col C: Weight (%), Col D: Deriv. Weight (%/°C)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temperature = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Filter data for x-axis range 100-700 if needed for plotting limits, 
# but usually we plot all data and just set limits. 
# However, finding peaks/residues should be done on relevant data or full data depending on definition.
# The prompt says "residue at nearest 800C" and "peak above 150C".
# We will use the full data to find these specific points, even if they fall outside the view, 
# though residue at 800 is outside 100-700. Wait, if x-range is 100-700, 800 is not visible.
# Let's check the instruction: "residue: the weight at the measured point nearest 800 °C... with a marker on the curve".
# If the axis range is 100-700, a marker at 800 won't be seen. 
# Usually, in such requests, if the range excludes the standard reference point, one might still calculate it, 
# but visually it's off-chart. Or perhaps the user wants to see the main degradation.
# I will calculate them from the full dataset. If the marker is outside the xlim, it won't show.
# Given the explicit request for x-range 100-700, I will respect that. 
# The residue at 800 will likely not appear in the plot area. 
# The peak > 150C will likely appear.

# Find Residue at ~800°C
idx_800 = np.argmin(np.abs(temperature - 800))
residue_val = weight[idx_800]
residue_temp = temperature[idx_800]

# Find Peak DTG above 150°C
mask_peak = temperature > 150
if np.any(mask_peak):
    # DTG is negative during mass loss. We want the highest magnitude of mass loss, which is the most negative value.
    # But the prompt says "highest DTG peak ... multiplied by -1 so its peaks point up".
    # So we look for the minimum value of original DTG (most negative) in the region > 150C.
    dtg_subset = dtg[mask_peak]
    temp_subset = temperature[mask_peak]
    
    min_dtg_idx = np.argmin(dtg_subset)
    peak_temp = temp_subset[min_dtg_idx]
    peak_dtg_val = dtg_subset[min_dtg_idx]
else:
    peak_temp = None
    peak_dtg_val = None

# Create Plot
fig, ax1 = plt.subplots(figsize=(8, 6))

# X-axis settings
ax1.set_xlim(100, 700)
ax1.set_xticks(np.arange(100, 701, 100))
ax1.set_xlabel("Temperature (°C)")

# Y1 Axis (Left) - Weight (%)
color_y1 = 'red'
ax1.plot(temperature, weight, color=color_y1, linewidth=3, label='Weight (%)')
ax1.set_ylabel("Weight (%)", color=color_y1)
ax1.tick_params(axis='y', labelcolor=color_y1)

# Y2 Axis (Right) - DTG
ax2 = ax1.twinx()
color_y2 = '#c0392b' # Standard red-ish for DTG, distinct from the pure red requested for y1? 
# User asked for y1 line to be red. Standard DTG is often different color. 
# Prompt default: y1 #1f4e9c (blue), y2 #c0392b (red).
# User override: y1 line thick(3) red.
# I'll keep y2 as default dark red/brown or similar to distinguish, or maybe black? 
# Let's stick to the default y2 color #c0392b unless specified otherwise. It's a reddish tone too. 
# To ensure contrast, since y1 is now bright red, maybe y2 should be a darker shade or blue? 
# The prompt doesn't specify y2 color. I will use the default #c0392b. If it clashes, it's per spec.
# Actually, let's look at the colors. y1 is Red. y2 default is #c0392b (Pomegranate). They are very similar.
# This might make it hard to distinguish. However, I must follow instructions. 
# Instruction: "y1 선 굵게(3) 빨간색으로 해주세용". No mention of y2 color change.
# I will proceed with default y2 color.

# Plot DTG (multiplied by -1 to point up)
ax2.plot(temperature, -dtg, color='#c0392b', linewidth=1.5, label='DTG (%/°C)')
ax2.set_ylabel("DTG (%/°C)", color='#c0392b')
ax2.tick_params(axis='y', labelcolor='#c0392b')

# Title
ax1.set_title("PE")

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

# Annotations
# Residue Marker
# Note: Since xlim is 100-700, and residue is at ~800, this marker will be outside the plot area.
# I will add it anyway as per logic, but it won't be visible.
ax1.plot(residue_temp, residue_val, 'o', color='black', markersize=6)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val), 
             xytext=(residue_temp+20, residue_val+5), fontsize=9, color='black')

# Peak Marker
if peak_temp is not None:
    # Check if peak is within view for annotation placement logic, though annotate works regardless
    ax1.plot(peak_temp, weight[np.argmin(np.abs(temperature - peak_temp))], 'v', color='green', markersize=6)
    # Annotate near the top of the DTG peak or on the weight curve? 
    # Prompt: "written like '600 °C', with a marker."
    # Usually placed near the feature. I'll place it near the weight curve corresponding to the peak temp.
    w_at_peak = weight[np.argmin(np.abs(temperature - peak_temp))]
    ax1.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, w_at_peak), 
                 xytext=(peak_temp+20, w_at_peak+10), fontsize=9, color='green')

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, "PE.png")
plt.savefig(out_path, dpi=300)
plt.close()
