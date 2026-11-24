import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B09_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

def plot_tga_sheet(sheet_name, df):
    # Extract columns based on standard TGA structure identified in preview
    x_col = "Temperature (°C)"
    y1_col = "Weight (%)"
    y2_col = "Deriv. Weight (%/°C)"
    
    if x_col not in df.columns or y1_col not in df.columns or y2_col not in df.columns:
        return

    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left y-axis (y1)
    # User request: line bold (3), red color
    color_y1 = 'red'
    ax1.plot(temp, weight, color=color_y1, linewidth=3, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Set x-axis range and ticks
    ax1.set_xlim(100, 700)
    ax1.set_xticks(np.arange(100, 701, 100))
    
    # Create secondary y-axis for DTG
    ax2 = ax1.twinx()
    # Plot DTG multiplied by -1 so peaks point up
    color_y2 = '#c0392b' # Standard dark red-ish for DTG usually, but let's stick to a distinct color or default blue/green if needed. 
    # The prompt says y1 is red. Let's make y2 a different color, e.g., blue or green, to distinguish.
    # Actually, standard TGA plots often use black/blue for DTG. Let's use a dark blue for contrast against the red Weight line.
    color_y2 = '#1f4e9c' 
    ax2.plot(temp, -dtg, color=color_y2, linewidth=1.5, label='DTG (-dW/dT)')
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_y2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14, fontweight='bold')
    
    # Find Residue at ~800°C
    # Since x-range is limited to 700 in display, we still calculate residue from full data near 800
    mask_800 = (temp >= 790) & (temp <= 810)
    if mask_800.any():
        idx_800 = np.argmin(np.abs(temp[mask_800] - 800)) + np.where(mask_800)[0][0]
        residue_val = weight[idx_800]
        residue_temp = temp[idx_800]
        
        # Only mark if within the visible x-range? Usually markers are good even if slightly off, 
        # but 800 is outside 100-700. 
        # The prompt asks for labels "unless user says otherwise". 
        # If the point is outside the view, adding a marker might look weird or be clipped.
        # However, standard practice is to show it if possible. Since 800 > 700, it won't be seen.
        # I will skip drawing the marker/text if it falls outside the xlim, or adjust logic.
        # Given the strict request "x축 범위 100~700", showing a label at 800 is impossible visually.
        # I will omit the residue label/marker if it's outside the plot area to avoid confusion/clipping issues.
        pass 

    # Find Peak above 150°C
    # We need to find the max of -dtg (which corresponds to min of dtg) where temp > 150
    mask_peak = (temp > 150) & (temp < 900) # Use full range for finding peak location
    if mask_peak.any():
        dtg_subset = dtg[mask_peak]
        temp_subset = temp[mask_peak]
        
        # Max peak in derivative weight loss means most negative dtg value
        # Or max of -dtg
        inv_dtg_subset = -dtg_subset
        max_idx_local = np.argmax(inv_dtg_subset)
        
        peak_temp = temp_subset[max_idx_local]
        peak_dtg_val = -dtg_subset[max_idx_local] # This is the positive height of the peak
        
        # Check if peak temp is within the displayed x-range (100-700)
        if 100 <= peak_temp <= 700:
            # Draw marker on the curve (on the right axis scale)
            ax2.plot(peak_temp, peak_dtg_val, 'o', color=color_y2, markersize=8)
            # Add text label
            ax2.text(peak_temp, peak_dtg_val * 1.05, f'{peak_temp:.0f} °C', 
                     color=color_y2, ha='center', va='bottom', fontsize=10, fontweight='bold')
            
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.05, 0.5))
    
    # Grid
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # Save
    out_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

# Load Excel file
xls = pd.ExcelFile(DATA_FILE)

# Process only PE sheet as requested
if 'PE' in xls.sheet_names:
    df_pe = pd.read_excel(xls, sheet_name='PE')
    plot_tga_sheet('PE', df_pe)

