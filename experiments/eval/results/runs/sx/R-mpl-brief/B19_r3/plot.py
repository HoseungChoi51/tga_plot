import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B19_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the PVC sheet
df = pd.read_excel(DATA_FILE, sheet_name='PVC')

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
dtg = df['Deriv. Weight (%/°C)'].values

# Calculate mass loss between 200°C and 400°C
# Find weight at 200°C and 400°C by interpolation or nearest point
def get_weight_at_temp(temp_arr, weight_arr, target_temp):
    # Find index closest to target_temp
    idx = np.argmin(np.abs(temp_arr - target_temp))
    return weight_arr[idx], temp_arr[idx]

w_200, t_200 = get_weight_at_temp(temp, weight, 200.0)
w_400, t_400 = get_weight_at_temp(temp, weight, 400.0)

mass_loss = w_200 - w_400  # positive value representing loss

# Standard TGA plot for PVC
fig, ax1 = plt.subplots(figsize=(8, 6))

color_y1 = '#1f4e9c'
color_y2 = '#c0392b'

ax1.plot(temp, weight, color=color_y1, label='Weight (%)', linewidth=1.5)
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_y1)
ax1.set_xlim(30, 900)
ax1.set_ylim(0, 105)

ax2 = ax1.twinx()
# Multiply DTG by -1 so peaks point up
ax2.plot(temp, -dtg, color=color_y2, label='DTG (%/°C)', linewidth=1.5)
ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color_y2)

# Title from sheet name
ax1.set_title('PVC', fontsize=14)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.02, 0.5), fontsize=10)

# Residue label: weight at nearest 800°C
idx_res = np.argmin(np.abs(temp - 800.0))
res_weight = weight[idx_res]
res_temp = temp[idx_res]
ax1.plot(res_temp, res_weight, 'o', color=color_y1, markersize=6)
ax1.annotate(f'Residue {res_weight:.1f}%', xy=(res_temp, res_weight),
             xytext=(res_temp - 150, res_weight + 15),
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10, color='black')

# Peak label: highest DTG peak above 150°C
mask = temp > 150
if mask.any():
    dtg_above = -dtg[mask]  # inverted DTG
    temps_above = temp[mask]
    peak_idx_local = np.argmax(dtg_above)
    peak_temp = temps_above[peak_idx_local]
    peak_dtg_val = dtg_above[peak_idx_local]
    
    # Get corresponding weight at peak temp
    idx_peak = np.argmin(np.abs(temp - peak_temp))
    w_at_peak = weight[idx_peak]
    
    ax2.plot(peak_temp, peak_dtg_val, 'o', color=color_y2, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_dtg_val),
                 xytext=(peak_temp + 50, peak_dtg_val * 0.8),
                 arrowprops=dict(arrowstyle='->', color='black'),
                 fontsize=10, color='black')

# Display mass loss annotation on the plot
# Draw vertical lines at 200 and 400°C
ax1.axvline(x=200, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
ax1.axvline(x=400, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

# Annotate the mass loss
mid_x = 300
mid_y = (w_200 + w_400) / 2
ax1.annotate(f'Mass Loss\n{mass_loss:.2f}%', xy=(mid_x, mid_y),
             xytext=(mid_x, mid_y + 20),
             ha='center', va='bottom',
             fontsize=11, fontweight='bold', color='darkgreen',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='darkgreen', alpha=0.8))

# Mark points at 200 and 400
ax1.plot(t_200, w_200, 's', color='darkgreen', markersize=7)
ax1.plot(t_400, w_400, 's', color='darkgreen', markersize=7)

plt.tight_layout()

out_path = os.path.join(OUT_DIR, 'PVC_mass_loss.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
