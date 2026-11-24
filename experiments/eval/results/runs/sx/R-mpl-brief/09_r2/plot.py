import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/09_r2/out"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read all sheets from the Excel file
xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(xl_file, sheet_name=sheet_name)
    
    # Identify columns based on the preview and standard TGA structure
    # Columns: A=Time, B=Temperature, C=Weight(%), D=D.W(%/C)
    try:
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dtg_col = 'D.W(%/C)'
        
        if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
            continue
            
        x = df[temp_col].values
        y1 = df[weight_col].values
        y2 = df[dtg_col].values
        
        # Filter out NaN values
        mask = ~(np.isnan(x) | np.isnan(y1) | np.isnan(y2))
        x = x[mask]
        y1 = y1[mask]
        y2 = y2[mask]
        
        if len(x) == 0:
            continue

        fig, ax1 = plt.subplots(figsize=(8, 6))
        
        # Plot Weight (%) on left axis (y1)
        color1 = '#1f4e9c'
        ax1.plot(x, y1, color=color1, label='Weight (%)')
        ax1.set_xlabel('Temperature (°C)', fontsize=10)
        ax1.set_ylabel('Weight (%)', color=color1, fontsize=10)
        ax1.tick_params(axis='y', labelcolor=color1, direction='out', labelsize=9)
        ax1.tick_params(axis='x', direction='out', labelsize=9)
        
        # Create second y-axis for DTG
        ax2 = ax1.twinx()
        color2 = '#c0392b'
        # Multiply DTG by -1 so peaks point up
        y2_neg = y2 * -1
        ax2.plot(x, y2_neg, color=color2, label='DTG (%/°C)')
        ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=10)
        ax2.tick_params(axis='y', labelcolor=color2, direction='out', labelsize=9)
        
        # Title is the sheet name
        ax1.set_title(sheet_name, fontsize=12)
        
        # Find Residue at ~800°C
        # Find index closest to 800
        idx_800 = np.argmin(np.abs(x - 800))
        residue_val = y1[idx_800]
        residue_temp = x[idx_800]
        
        # Add marker and text for residue
        ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=5)
        ax1.text(residue_temp, residue_val, f'Residue {residue_val:.1f}%', 
                 verticalalignment='bottom', horizontalalignment='right', 
                 color=color1, fontsize=9, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        
        # Find Peak temperature above 150°C
        # Filter data where temp > 150
        mask_peak = x > 150
        if np.any(mask_peak):
            x_peak_region = x[mask_peak]
            y2_neg_peak_region = y2_neg[mask_peak]
            
            # Find max of inverted DTG (which corresponds to most negative original DTG)
            idx_max_dtg = np.argmax(y2_neg_peak_region)
            peak_temp = x_peak_region[idx_max_dtg]
            peak_val_neg = y2_neg_peak_region[idx_max_dtg]
            
            # Add marker and text for peak
            ax2.plot(peak_temp, peak_val_neg, 'v', color=color2, markersize=5)
            ax2.text(peak_temp, peak_val_neg, f'{peak_temp:.0f} °C', 
                     verticalalignment='bottom', horizontalalignment='center', 
                     color=color2, fontsize=9, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        
        # Legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=9)
        
        # Grid
        ax1.grid(True, linestyle='--', alpha=0.5)
        
        # Adjust layout
        fig.tight_layout()
        
        # Save figure
        safe_sheet_name = "".join([c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')]).rstrip()
        filename = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
        plt.savefig(filename, dpi=300)
        plt.close(fig)
        
    except Exception as e:
        print(f"Error processing sheet {sheet_name}: {e}")
        continue
