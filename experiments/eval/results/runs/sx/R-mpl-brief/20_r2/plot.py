import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/20_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on typical TGA structure or the provided preview logic
    # Preview suggests: B=Temperature, C=Weight(%), D=D.W(%/C)
    # Let's map them robustly
    cols = df.columns.tolist()
    
    # Heuristic to find columns if names vary slightly, but here they are specific
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in str(c):
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            dtg_col = c
            
    # Fallback based on position if names don't match exactly (A=time, B=temp, C=weight, D=dtg)
    if temp_col is None and len(cols) >= 2: temp_col = cols[1]
    if weight_col is None and len(cols) >= 3: weight_col = cols[2]
    if dtg_col is None and len(cols) >= 4: dtg_col = cols[3]
    
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Clean data: remove NaNs
    mask = ~np.isnan(x) & ~np.isnan(y1) & ~np.isnan(y2)
    x = x[mask]
    y1 = y1[mask]
    y2 = y2[mask]
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color1 = '#1f4e9c'
    ax1.plot(x, y1, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('Weight (%)', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Create secondary axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    ax2.plot(x, -y2, color=color2, label='DTG (-%/°C)')
    ax2.set_ylabel('DTG (-%/°C)', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Fill area between 300 and 450 °C with light gray
    fill_min = 300
    fill_max = 450
    
    # Find indices where temperature is within range
    idx_start = np.searchsorted(x, fill_min)
    idx_end = np.searchsorted(x, fill_max)
    
    # Ensure indices are within bounds
    if idx_start < len(x) and idx_end > 0:
        # Adjust start index to be the first point >= fill_min
        # searchsorted returns insertion point. 
        # If x[idx_start] == fill_min, it's fine.
        # We want to fill from fill_min to fill_max.
        
        # Get the subset of x that falls in [fill_min, fill_max]
        # To make a clean polygon, we can just use axvspan which is easier and cleaner
        ax1.axvspan(fill_min, fill_max, alpha=0.3, color='gray', zorder=0)
    
    # Title
    ax1.set_title(sheet_name)
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')
    
    # Residue Label (nearest 800 C)
    target_residue_temp = 800
    if np.any(x <= target_residue_temp):
        # Find closest point to 800C
        idx_res = np.argmin(np.abs(x - target_residue_temp))
        res_weight = y1[idx_res]
        res_temp = x[idx_res]
        ax1.plot(res_temp, res_weight, 'o', color=color1, markersize=6)
        ax1.annotate(f'Residue {res_weight:.1f}%', 
                     xy=(res_temp, res_weight), 
                     xytext=(10, 10), textcoords='offset points',
                     color=color1, fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color1, lw=0.5))
                     
    # Peak Label (highest DTG peak above 150 C)
    # Note: y2 is negative during mass loss. We plotted -y2. 
    # So we look for max(-y2) i.e., min(y2) in original scale, restricted to x > 150.
    mask_peak = x > 150
    if np.any(mask_peak):
        y2_filtered = y2[mask_peak]
        x_filtered = x[mask_peak]
        
        # Original DTG is negative. The "peak" in magnitude is the most negative value.
        # On our plot (-y2), this corresponds to the maximum value.
        # But let's stick to finding the extremum of the plotted curve (-y2) or original?
        # Standard TGA peak is defined by the minimum of dW/dT (most negative slope).
        idx_min_dtg = np.argmin(y2_filtered) # Most negative original DTG
        peak_temp = x_filtered[idx_min_dtg]
        peak_val_original = y2_filtered[idx_min_dtg]
        
        # Plot marker on the right axis (ax2) at -peak_val_original
        ax2.plot(peak_temp, -peak_val_original, 'o', color=color2, markersize=6)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_val_original), 
                     xytext=(10, 10), textcoords='offset points',
                     color=color2, fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color2, lw=0.5))

    # Grid
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Save
    safe_sheet_name = "".join([i if i.isalnum() or i in ['-', '_', ' '] else '_' for i in sheet_name])
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
