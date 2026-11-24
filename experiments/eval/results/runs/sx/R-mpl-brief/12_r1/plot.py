import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configure fonts for Korean text
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/12_r1/out"

def plot_tga_sheet(df, sheet_name, out_path):
    # Identify columns based on standard TGA structure or heuristics
    cols = df.columns.tolist()
    
    # Try to find Temperature, Weight, and DTG columns
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl or 'temperature' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or ('derivative' in cl and 'weight' in cl):
            dtg_col = c
            
    # Fallback if names are ambiguous
    if temp_col is None and len(cols) >= 2:
        # Assume B is temp if A is time
        if 'time' in str(cols[0]).lower():
            temp_col = cols[1]
            weight_col = cols[2] if len(cols) > 2 else None
            dtg_col = cols[3] if len(cols) > 3 else None
        else:
            temp_col = cols[0]
            weight_col = cols[1] if len(cols) > 1 else None
            dtg_col = cols[2] if len(cols) > 2 else None

    if temp_col is None or weight_col is None:
        print(f"Skipping {sheet_name}: Could not identify required columns.")
        return

    x_data = df[temp_col].dropna().values
    y1_data = df[weight_col].dropna().values
    
    # Align lengths if dropna removed different amounts (rare but safe)
    min_len = min(len(x_data), len(y1_data))
    x_data = x_data[:min_len]
    y1_data = y1_data[:min_len]
    
    y2_data = None
    if dtg_col:
        y2_raw = df[dtg_col].dropna().values
        # Align with x_data
        if len(y2_raw) >= min_len:
             y2_data = y2_raw[:min_len]
        elif len(y2_raw) > 0:
             # If shorter, try to align by index logic or just truncate/pad? 
             # Usually they match. Let's assume matching indices for simplicity if possible,
             # otherwise use the available data.
             y2_data = y2_raw

    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color1 = '#1f4e9c'
    ax1.plot(x_data, y1_data, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot DTG on right axis
    if y2_data is not None:
        ax2 = ax1.twinx()
        color2 = '#c0392b'
        # Multiply by -1 so peaks point up
        ax2.plot(x_data, [-val for val in y2_data], color=color2, label='DTG (-%)')
        ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Find Peak above 150°C
        mask_peak = x_data > 150
        if np.any(mask_peak):
            x_peak_region = x_data[mask_peak]
            y_peak_region = np.array([-v for v in y2_data])[mask_peak]
            
            max_idx = np.argmax(y_peak_region)
            peak_temp = x_peak_region[max_idx]
            peak_val = y_peak_region[max_idx]
            
            # Mark peak
            ax2.scatter([peak_temp], [peak_val], color=color2, zorder=5)
            ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_val), 
                         xytext=(peak_temp + 20, peak_val * 1.1),
                         arrowprops=dict(arrowstyle='->', color=color2),
                         fontsize=10, color=color2)
                         
        # Legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')
    else:
        ax1.legend(loc='center left')

    # Add Vertical Reference Line at 450°C
    ax1.axvline(x=450, color='gray', linestyle='--', linewidth=1.5)
    ax1.text(450, ax1.get_ylim()[1] * 0.95, '산화 시작', rotation=90, verticalalignment='top', horizontalalignment='right', color='black', fontsize=12)

    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Residue Label (nearest to 800°C)
    # Note: Some sheets might not go up to 800°C. We take the nearest point to 800 within range.
    target_temp = 800
    idx_residue = np.argmin(np.abs(x_data - target_temp))
    residue_temp = x_data[idx_residue]
    residue_weight = y1_data[idx_residue]
    
    # Only add marker if it's reasonably close to 800 or if the curve ends there
    # The prompt says "nearest 800", so we always mark the nearest point.
    ax1.scatter([residue_temp], [residue_weight], color=color1, zorder=5)
    ax1.annotate(f'Residue {residue_weight:.1f}%', xy=(residue_temp, residue_weight),
                 xytext=(residue_temp - 50, residue_weight + 5),
                 arrowprops=dict(arrowstyle='->', color=color1),
                 fontsize=10, color=color1)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(OUT_DIR, exist_ok=True)
    
    xls = pd.ExcelFile(DATA_FILE)
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Clean column names if needed
        df.columns = [str(c).strip() for c in df.columns]
        
        # Sanitize filename
        safe_sheet_name = "".join([i if i.isalnum() or i in ['-', '_'] else "_" for i in sheet_name])
        out_file = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
        
        plot_tga_sheet(df, sheet_name, out_file)
