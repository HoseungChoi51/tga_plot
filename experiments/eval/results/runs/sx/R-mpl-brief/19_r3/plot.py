import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# Configure font for Korean support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/19_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Global settings from user request
TEXT_COLOR = '#808080'  # Gray
TEXT_SIZE = 13

def plot_tga_sheet(df, sheet_name):
    """Plot TGA data for a single sheet."""
    
    # Identify columns based on standard TGA structure
    # x: Temperature, y1: Weight(%), y2: D.W(%/C)
    x_col = None
    y1_col = None
    y2_col = None
    
    cols = df.columns.tolist()
    for c in cols:
        cl = str(c).lower()
        if 'temperature' in cl or 'temp' in cl:
            x_col = c
        elif 'weight' in cl and '%' in cl:
            y1_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            y2_col = c
            
    # Fallback to indices if names aren't clear (based on preview: B, C, D)
    if x_col is None: x_col = cols[1]
    if y1_col is None: y1_col = cols[2]
    if y2_col is None: y2_col = cols[3]
    
    x_data = df[x_col].values
    y1_data = df[y1_col].values
    y2_data = df[y2_col].values
    
    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis (y1)
    color_y1 = '#1f4e9c'
    line1, = ax1.plot(x_data, y1_data, color=color_y1, linewidth=1.5, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=TEXT_SIZE, color=TEXT_COLOR)
    ax1.set_ylabel('Weight (%)', fontsize=TEXT_SIZE, color=TEXT_COLOR)
    ax1.tick_params(axis='both', which='major', labelsize=TEXT_SIZE, colors=TEXT_COLOR)
    ax1.tick_params(axis='both', which='minor', labelsize=TEXT_SIZE-2, colors=TEXT_COLOR)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    color_y2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    dtg_inverted = -y2_data
    line2, = ax2.plot(x_data, dtg_inverted, color=color_y2, linewidth=1.5, linestyle='--', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', fontsize=TEXT_SIZE, color=TEXT_COLOR)
    ax2.tick_params(axis='both', which='major', labelsize=TEXT_SIZE, colors=TEXT_COLOR)
    ax2.tick_params(axis='both', which='minor', labelsize=TEXT_SIZE-2, colors=TEXT_COLOR)
    
    # Title
    ax1.set_title(sheet_name, fontsize=TEXT_SIZE+2, color=TEXT_COLOR, pad=10)
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    legend = ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.02, 0.5), fontsize=TEXT_SIZE, frameon=False)
    for text in legend.get_texts():
        text.set_color(TEXT_COLOR)
        
    # --- Residue Calculation ---
    # Find weight at temperature nearest to 800°C
    target_temp = 800.0
    idx_residue = np.argmin(np.abs(x_data - target_temp))
    residue_val = y1_data[idx_residue]
    temp_residue = x_data[idx_residue]
    
    # Mark residue on the curve
    ax1.plot(temp_residue, residue_val, 'o', color=color_y1, markersize=6)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(temp_residue, residue_val), 
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=TEXT_SIZE, color=TEXT_COLOR,
                 arrowprops=dict(arrowstyle='->', color=TEXT_COLOR, lw=1))
                 
    # --- Peak Calculation ---
    # Find highest DTG peak above 150°C
    mask_peak = x_data > 150.0
    if np.any(mask_peak):
        x_filtered = x_data[mask_peak]
        dtg_filtered = dtg_inverted[mask_peak] # Using inverted DTG
        
        # Find index of max value in filtered data
        idx_max_dtg_local = np.argmax(dtg_filtered)
        peak_temp = x_filtered[idx_max_dtg_local]
        peak_val_inv = dtg_filtered[idx_max_dtg_local]
        
        # Map back to original index if needed, but we have the temp directly
        # Mark peak on the DTG curve (which is on ax2)
        # We need to find the corresponding y-value on the right axis scale
        # Since we plotted dtg_inverted on ax2, the value is peak_val_inv
        
        ax2.plot(peak_temp, peak_val_inv, 'v', color=color_y2, markersize=6)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_val_inv), 
                     xytext=(-10, 10), textcoords='offset points',
                     fontsize=TEXT_SIZE, color=TEXT_COLOR,
                     arrowprops=dict(arrowstyle='->', color=TEXT_COLOR, lw=1))
    
    # Grid
    ax1.grid(True, linestyle=':', alpha=0.5, color=TEXT_COLOR)
    
    # Save plot
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).strip()
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

# Load Excel file
try:
    xls = pd.ExcelFile(DATA_FILE)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Drop rows where key columns are NaN if necessary, though TGA data is usually clean
        df.dropna(subset=[df.columns[1], df.columns[2]], inplace=True)
        plot_tga_sheet(df, sheet_name)
except Exception as e:
    print(f"Error processing file: {e}")
