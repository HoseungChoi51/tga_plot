import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/10_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on standard TGA structure or names
    cols = df.columns.tolist()
    
    # Heuristic to find columns if names vary slightly, though preview gives specific names
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            x_col = c
        elif 'weight' in cl and '%' in cl:
            y1_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            y2_col = c
            
    # Fallback to indices if heuristics fail (based on preview: B, C, D are 1, 2, 3 index-wise if A is 0)
    if x_col is None and len(cols) >= 4:
        x_col = cols[1] # Temperature
    if y1_col is None and len(cols) >= 5:
        y1_col = cols[2] # Weight(%)
    if y2_col is None and len(cols) >= 6:
        y2_col = cols[3] # D.W(%/C)
        
    if x_col is None or y1_col is None or y2_col is None:
        continue
        
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left y-axis
    color1 = '#1f4e9c'
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    line1, = ax1.plot(temp, weight, color=color1, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Create second y-axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
    # Multiply by -1 so peaks point up
    line2, = ax2.plot(temp, -dtg, color=color2, label='DTG (-1)')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # Grid
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # --- Calculate Residue at 700 °C with 2 decimal places ---
    target_temp_residue = 700.0
    
    # Interpolate weight at exactly 700 °C
    # Filter valid data points
    valid_mask = ~np.isnan(temp) & ~np.isnan(weight)
    t_valid = temp[valid_mask]
    w_valid = weight[valid_mask]
    
    if len(t_valid) > 0:
        # Sort just in case
        sort_idx = np.argsort(t_valid)
        t_sorted = t_valid[sort_idx]
        w_sorted = w_valid[sort_idx]
        
        # Check if 700 is within range
        if t_sorted.min() <= target_temp_residue <= t_sorted.max():
            f_interp = interp1d(t_sorted, w_sorted, kind='linear')
            residue_val = f_interp(target_temp_residue)
            
            # Find the closest actual data point for marker placement
            idx_closest = np.argmin(np.abs(t_sorted - target_temp_residue))
            marker_t = t_sorted[idx_closest]
            marker_w = w_sorted[idx_closest]
            
            # Format string: "Residue X.XX%"
            res_str = f"Residue {residue_val:.2f}%"
            
            # Add annotation and marker
            ax1.plot(marker_t, marker_w, 'o', color=color1, markersize=8)
            ax1.annotate(res_str, xy=(marker_t, marker_w), 
                         xytext=(10, 10), textcoords='offset points',
                         fontsize=10, color=color1,
                         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color1, alpha=0.8))
        else:
            print(f"Warning: 700°C is outside temperature range for sheet {sheet_name}")

    # --- Calculate Peak above 150 °C ---
    # We look for the highest peak of -dtg (since we plotted -dtg, max value is the peak)
    # Only consider temperatures > 150 °C
    mask_peak = (temp > 150) & (~np.isnan(dtg))
    
    if np.any(mask_peak):
        t_peak_region = temp[mask_peak]
        dtg_peak_region = dtg[mask_peak]
        
        # Since we want the peak where mass loss is maximum, dtg is most negative.
        # So min(dtg) corresponds to the largest magnitude of mass loss rate.
        # Alternatively, looking at -dtg, it's the max(-dtg).
        
        # Let's use the original dtg values to find the minimum (most negative)
        idx_min_dtg = np.argmin(dtg_peak_region)
        peak_temp = t_peak_region[idx_min_dtg]
        peak_dtg_val = dtg_peak_region[idx_min_dtg]
        
        # Marker on the DTG curve (which is plotted as -dtg on ax2)
        # The y-value on ax2 is -peak_dtg_val
        marker_y_ax2 = -peak_dtg_val
        
        # Find closest actual point for consistency
        idx_closest_peak = np.argmin(np.abs(temp - peak_temp))
        marker_t_peak = temp[idx_closest_peak]
        marker_dtg_actual = dtg[idx_closest_peak]
        marker_y_ax2_actual = -marker_dtg_actual
        
        # Format string: "XXX °C"
        peak_str = f"{int(round(peak_temp))} °C"
        
        # Add annotation and marker on ax2
        ax2.plot(marker_t_peak, marker_y_ax2_actual, 'v', color=color2, markersize=8)
        ax2.annotate(peak_str, xy=(marker_t_peak, marker_y_ax2_actual),
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=10, color=color2,
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color2, alpha=0.8))

    # Adjust layout
    plt.tight_layout()
    
    # Save file
    safe_sheet_name = sheet_name.replace(" ", "_").replace("/", "_")
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

print("Plots generated successfully.")
