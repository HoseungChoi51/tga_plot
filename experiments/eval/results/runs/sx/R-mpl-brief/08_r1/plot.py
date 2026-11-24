import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/08_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

def sanitize_filename(name):
    # Remove characters that are not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on the preview structure
    # Assuming standard TGA structure: Time, Temperature, Weight(%), D.W(%/C)
    # We look for columns containing keywords or use positional if names match preview
    cols = df.columns.tolist()
    
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temperature' in c_lower or 'temp' in c_lower:
            x_col = c
        elif 'weight' in c_lower and 'd.w' not in c_lower and 'dtg' not in c_lower and 'derivative' not in c_lower:
            y1_col = c
        elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower or ('weight' in c_lower and '%' in str(c)):
             # Be careful with "Weight(%)" vs "D.W(%/C)". 
             # In preview: Col C is Weight(%), Col D is D.W(%/C)
             # Let's refine detection
             pass

    # Refine detection based on typical order and specific names from preview
    # Preview shows: A:Time, B:Temperature, C:Weight(%), D:D.W(%/C)
    # Let's try to map by position if names are ambiguous, but here names seem distinct enough
    
    temp_cols = [c for c in cols if 'temperature' in str(c).lower()]
    weight_cols = [c for c in cols if 'weight' in str(c).lower() and 'd.w' not in str(c).lower() and 'dtg' not in str(c).lower()]
    dtg_cols = [c for c in cols if 'd.w' in str(c).lower() or 'dtg' in str(c).lower() or 'derivative' in str(c).lower()]
    
    if len(temp_cols) > 0: x_col = temp_cols[0]
    if len(weight_cols) > 0: y1_col = weight_cols[0]
    if len(dtg_cols) > 0: y2_col = dtg_cols[0]
    
    # Fallback to positional if needed (assuming A,B,C,D structure)
    if x_col is None and len(cols) >= 2: x_col = cols[1]
    if y1_col is None and len(cols) >= 3: y1_col = cols[2]
    if y2_col is None and len(cols) >= 4: y2_col = cols[3]

    if x_col is None or y1_col is None or y2_col is None:
        continue
        
    data_x = df[x_col].values
    data_y1 = df[y1_col].values
    data_y2 = df[y2_col].values
    
    # Filter valid data
    mask = ~np.isnan(data_x) & ~np.isnan(data_y1) & ~np.isnan(data_y2)
    data_x = data_x[mask]
    data_y1 = data_y1[mask]
    data_y2 = data_y2[mask]
    
    if len(data_x) == 0:
        continue

    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color1 = '#1f4e9c'
    line1 = ax1.plot(data_x, data_y1, color=color1, label='Weight (%)')
    ax1.set_xlabel('온도 (°C)', fontsize=12)
    ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    data_y2_inv = -data_y2
    line2 = ax2.plot(data_x, data_y2_inv, color=color2, label='DTG (%/°C)')
    ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Find Residue at 800°C
    # Find index closest to 800
    idx_800 = np.argmin(np.abs(data_x - 800))
    residue_val = data_y1[idx_800]
    residue_temp = data_x[idx_800]
    
    # Add marker and text for residue
    ax1.scatter(residue_temp, residue_val, color=color1, zorder=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 20, residue_val + 5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 fontsize=10, color=color1)
                 
    # Find Peak temperature above 150°C
    # Mask for temp > 150
    mask_peak = data_x > 150
    if np.any(mask_peak):
        y2_masked = data_y2_inv[mask_peak]
        x_masked = data_x[mask_peak]
        
        # Find max of inverted DTG (which corresponds to min original DTG, i.e., steepest loss)
        idx_max_dtg = np.argmax(y2_masked)
        peak_temp = x_masked[idx_max_dtg]
        peak_val_inv = y2_masked[idx_max_dtg]
        
        # Add marker and text for peak
        ax2.scatter(peak_temp, peak_val_inv, color=color2, zorder=5)
        ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_val_inv), 
                     xytext=(peak_temp + 20, peak_val_inv * 0.8), # Adjust text position relative to right axis scale
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     fontsize=10, color=color2)
    
    # Legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # Save
    safe_sheet_name = sanitize_filename(sheet_name)
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
