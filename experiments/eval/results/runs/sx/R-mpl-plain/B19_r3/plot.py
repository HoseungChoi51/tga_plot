import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B19_r3/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read PVC sheet
df_pvc = pd.read_excel(DATA_FILE, sheet_name='PVC')

# Extract relevant columns
temp = df_pvc['Temperature (°C)'].values
weight = df_pvc['Weight (%)'].values

# Define temperature range
t_min = 200
t_max = 400

# Find indices for the temperature range
mask = (temp >= t_min) & (temp <= t_max)
temp_range = temp[mask]
weight_range = weight[mask]

if len(temp_range) == 0:
    raise ValueError("No data found in the specified temperature range.")

# Get weight at start and end of the range
# Since data might not have exact points at 200 and 400, we interpolate or take closest
# Let's find the closest points to be safe, but interpolation is better for accuracy if needed.
# For simplicity and robustness with discrete TGA data, let's use linear interpolation.

from scipy.interpolate import interp1d

# Create interpolation function
interp_func = interp1d(temp, weight, kind='linear', fill_value="extrapolate")

w_200 = interp_func(t_min)
w_400 = interp_func(t_max)

mass_loss = w_200 - w_400

print(f"Weight at {t_min}°C: {w_200:.4f}%")
print(f"Weight at {t_max}°C: {w_400:.4f}%")
print(f"Mass loss between {t_min}°C and {t_max}°C: {mass_loss:.4f}%")

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight vs Temperature
ax1.plot(temp, weight, color='blue', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, linestyle='--', alpha=0.5)

# Highlight the region between 200 and 400 °C
ax1.axvspan(t_min, t_max, alpha=0.2, color='red', label=f'{t_min}-{t_max} °C Region')

# Add vertical lines at 200 and 400 °C
ax1.axvline(x=t_min, color='red', linestyle=':', linewidth=1)
ax1.axvline(x=t_max, color='red', linestyle=':', linewidth=1)

# Mark the specific points on the curve
ax1.plot([t_min], [w_200], 'ro', markersize=8, zorder=5)
ax1.plot([t_max], [w_400], 'ro', markersize=8, zorder=5)

# Annotate the mass loss value
text_str = f'Mass Loss ({t_min}-{t_max}°C): {mass_loss:.2f}%'
ax1.annotate(text_str, xy=((t_min + t_max)/2, (w_200 + w_400)/2), 
             xytext=(50, 50), textcoords='offset points',
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'),
             fontsize=12, color='darkred',
             bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7))

# Second Y-axis for Derivative Weight
df_pvc_deriv = df_pvc[['Temperature (°C)', 'Deriv. Weight (%/°C)']]
deriv_weight = df_pvc_deriv['Deriv. Weight (%/°C)'].values

ax2 = ax1.twinx()
ax2.plot(temp, deriv_weight, color='green', linestyle='--', label='Deriv. Weight (%/°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)', color='green', fontsize=12)
ax2.tick_params(axis='y', labelcolor='green')

# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', fontsize=10)

ax1.set_title('TGA Curve for PVC: Mass Loss Analysis (200°C - 400°C)', fontsize=14)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "pvc_mass_loss_analysis.png")
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Plot saved to {output_path}")
