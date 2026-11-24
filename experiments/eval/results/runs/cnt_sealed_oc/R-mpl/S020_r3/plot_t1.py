import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# File paths and labels
files = [
    ("data/raman/R1-260326-1.csv", "R1-260326-1"),
    ("data/raman/R2-260616-1.csv", "R2-260616-1"),
    ("data/raman/R4-260721-1.csv", "R4-260721-1")
]

# Parameters for baseline and normalization
baseline_left_center = 1100
baseline_right_center = 1800
baseline_window = 10
g_band_min = 1550
g_band_max = 1620
plot_xmin = 1000
plot_xmax = 2000

fig, ax = plt.subplots(figsize=(10, 6))

for file_path, label in files:
    # Read data
    df = pd.read_csv(file_path)
    
    # Identify columns (assuming first column is Raman Shift, second is Intensity based on preview)
    shift_col = df.columns[0]
    int_col = df.columns[1]
    
    shifts = df[shift_col].values
    intensities = df[int_col].values
    
    # Function to get average intensity in a window around a center value
    def get_baseline_point(center, width):
        mask = (shifts >= center - width) & (shifts <= center + width)
        if np.sum(mask) == 0:
            return np.nan
        return np.mean(intensities[mask])
    
    y_left = get_baseline_point(baseline_left_center, baseline_window)
    y_right = get_baseline_point(baseline_right_center, baseline_window)
    
    if np.isnan(y_left) or np.isnan(y_right):
        continue
        
    # Create linear baseline
    # Line equation: y = m*x + c
    m = (y_right - y_left) / (baseline_right_center - baseline_left_center)
    c = y_left - m * baseline_left_center
    
    # Subtract baseline from original intensities
    corrected_intensities = intensities - (m * shifts + c)
    
    # Find G band maximum within 1550-1620 cm-1 range
    g_mask = (shifts >= g_band_min) & (shifts <= g_band_max)
    if np.sum(g_mask) == 0:
        continue
        
    g_max_val = np.max(corrected_intensities[g_mask])
    
    if g_max_val == 0 or np.isnan(g_max_val):
        normalized_intensities = corrected_intensities
    else:
        normalized_intensities = corrected_intensities / g_max_val
        
    # Plot only the requested range 1000-2000 cm-1
    plot_mask = (shifts >= plot_xmin) & (shifts <= plot_xmax)
    ax.plot(shifts[plot_mask], normalized_intensities[plot_mask], label=label, linewidth=1.5)

ax.set_xlabel("Raman Shift (cm⁻¹)")
ax.set_ylabel("Normalized Intensity (a.u.)")
ax.set_title("G-band Normalized Raman Spectra (Baseline Corrected)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)
ax.set_xlim(plot_xmin, plot_xmax)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "raman_normalized_overlay.png"), dpi=300)
plt.close()
