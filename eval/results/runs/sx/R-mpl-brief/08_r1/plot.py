import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/08_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read Excel file with all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA structure from preview
    # x = Temperature (col B), y1 = Weight(%) (col C), y2 = D.W(%/C) (col D)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'temperature' in col_str or 'temp' in col_str:
            temp_col = col
        elif 'weight' in col_str and '%' in col_str:
            weight_col = col
        elif 'd.w' in col_str or 'dtg' in col_str or 'derivative' in col_str:
            dtg_col = col
            
    # Fallback to positional if names not found clearly
    if temp_col is None:
        temp_col = df.columns[1] # Column B
    if weight_col is None:
        weight_col = df.columns[2] # Column C
    if dtg_col is None:
        dtg_col = df.columns[3] # Column D
        
    x_data = df[temp_col].dropna().values
    y1_data = df[weight_col].dropna().values
    y2_data = df[dtg_col].dropna().values
    
    # Ensure lengths match after dropna
    min_len = min(len(x_data), len(y1_data), len(y2_data))
    x_data = x_data[:min_len]
    y1_data = y1_data[:min_len]
    y2_data = y2_data[:min_len]
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot Weight (%) on left y-axis
    color1 = '#1f4e9c'
    ax1.set_xlabel('온도 (°C)', fontsize=12)
    ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
    line1, = ax1.plot(x_data, y1_data, color=color1, label='Weight (%)')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
    # Multiply by -1 so peaks point up
    line2, = ax2.plot(x_data, -y2_data, color=color2, label='DTG (-dW/dT)')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title is the sheet name
    ax1.set_title(sheet_name, fontsize=14, pad=10)
    
    # Legend at center left
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5))
    
    # Calculate Residue at nearest 800°C
    # Find index closest to 800
    idx_800 = np.argmin(np.abs(x_data - 800))
    residue_val = y1_data[idx_800]
    residue_temp = x_data[idx_800]
    
    # Add residue marker and label
    ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=6)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 50, residue_val + 5),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color=color1)
                 
    # Calculate Peak temperature (highest DTG peak above 150°C)
    # We look for the minimum of original y2_data (most negative) because we plot -y2
    # Or simply find max of plotted -y2_data where x > 150
    mask = x_data > 150
    if np.any(mask):
        y2_plot_vals = -y2_data[mask]
        x_masked = x_data[mask]
        
        # Find index of maximum value in the masked array
        max_idx_in_masked = np.argmax(y2_plot_vals)
        peak_temp = x_masked[max_idx_in_masked]
        peak_dtg_val = y2_plot_vals[max_idx_in_masked]
        
        # Get corresponding weight at this temperature for context if needed, but we mark on DTG curve (ax2)
        # The prompt says "with a marker", usually on the curve it belongs to.
        # Since peak is defined by DTG, marker goes on ax2.
        
        ax2.plot(peak_temp, peak_dtg_val, 'v', color=color2, markersize=6)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_dtg_val), 
                     xytext=(peak_temp + 50, peak_dtg_val * 0.8),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                     fontsize=10, color=color2)
                     
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = "".join([c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')]).rstrip()
    output_filename = f"{safe_sheet_name}.png"
    output_path = os.path.join(OUT_DIR, output_filename)
    
    plt.savefig(output_path, dpi=300)
    plt.close(fig)

print("Plots generated successfully.")
