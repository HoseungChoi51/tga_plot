import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configure fonts for Korean support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/10_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

def plot_tga_sheet(sheet_name, df):
    """
    Plots TGA and DTG curves for a given DataFrame.
    Residue is calculated at 700 °C with 2 decimal places.
    Peak is the highest DTG peak above 150 °C.
    """
    # Identify columns based on standard TGA structure inferred from preview
    # x: Temperature (col B), y1: Weight(%) (col C), y2: D.W(%/C) (col D)
    cols = df.columns
    
    # Heuristic to find columns if names vary slightly, but using known structure from preview
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temp' in c_lower:
            temp_col = c
        elif 'weight' in c_lower or '%' in c_lower:
            if 'd.w' not in c_lower and 'derivative' not in c_lower:
                weight_col = c
        elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower:
            dtg_col = c
            
    # Fallback to indices if heuristics fail (based on preview: B=Temp, C=Weight, D=DTG)
    if temp_col is None and len(df.columns) >= 2: temp_col = df.columns[1]
    if weight_col is None and len(df.columns) >= 3: weight_col = df.columns[2]
    if dtg_col is None and len(df.columns) >= 4: dtg_col = df.columns[3]
    
    if temp_col is None or weight_col is None or dtg_col is None:
        return

    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Filter valid data points
    mask = ~np.isnan(x) & ~np.isnan(y1) & ~np.isnan(y2)
    x = x[mask]
    y1 = y1[mask]
    y2 = y2[mask]
    
    if len(x) == 0:
        return

    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) - Left Axis
    color1 = '#1f4e9c'
    line1, = ax1.plot(x, y1, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Create secondary axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    # Invert DTG so peaks point up
    line2, = ax2.plot(x, -y2, color=color2, label='DTG (-D.W %/°C)')
    ax2.set_ylabel('DTG (-D.W %/°C)', color=color2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    title_text = sheet_name
    ax1.set_title(title_text, fontsize=14, fontweight='bold')
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5), framealpha=0.9)
    
    # --- Calculate Residue at 700 °C ---
    target_temp_residue = 700.0
    # Find index closest to 700°C
    idx_residue = np.argmin(np.abs(x - target_temp_residue))
    residue_val = y1[idx_residue]
    residue_temp = x[idx_residue]
    
    # Format residue string: "Residue X.XX%"
    residue_str = f"Residue {residue_val:.2f}%"
    
    # Mark residue point
    ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=6)
    ax1.annotate(residue_str, 
                 xy=(residue_temp, residue_val), 
                 xytext=(10, 10), textcoords='offset points',
                 color=color1, fontsize=10, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=color1))
                 
    # --- Calculate Peak above 150 °C ---
    # We look for the maximum of the inverted DTG (which corresponds to the most negative original DTG, i.e., max mass loss rate)
    # The user asks for "highest DTG peak". In TGA context, this usually means the peak of the derivative curve (mass loss rate).
    # Since we plotted -y2, the peak is the local maximum of -y2 where Temp > 150.
    
    mask_peak = x > 150
    if np.any(mask_peak):
        x_peak_range = x[mask_peak]
        y2_inv_peak_range = -y2[mask_peak] # This is the plotted DTG value
        
        # Find index of maximum in the filtered range
        idx_max_in_filtered = np.argmax(y2_inv_peak_range)
        
        # Get actual temperature and original DTG value for annotation
        peak_temp = x_peak_range[idx_max_in_filtered]
        peak_dtg_original = y2[mask_peak][idx_max_in_filtered]
        
        # The annotation should show the temperature like "600 °C"
        peak_str = f"{peak_temp:.0f} °C"
        
        # Mark peak on the DTG curve (right axis)
        # Note: The marker needs to be placed on ax2
        ax2.plot(peak_temp, -peak_dtg_original, 'v', color=color2, markersize=8)
        ax2.annotate(peak_str,
                     xy=(peak_temp, -peak_dtg_original),
                     xytext=(-10, -15), textcoords='offset points',
                     color=color2, fontsize=10, fontweight='bold',
                     ha='right', va='top',
                     arrowprops=dict(arrowstyle='->', color=color2))
    else:
        # If no data above 150, skip peak annotation
        pass

    # Save figure
    safe_filename = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).strip().replace(' ', '_')
    out_path = os.path.join(OUT_DIR, f"{safe_filename}.png")
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

# Load Excel file
try:
    xl_file = pd.ExcelFile(DATA_FILE)
    sheet_names = xl_file.sheet_names
    
    for sheet in sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=0)
        plot_tga_sheet(sheet, df)
        
except Exception as e:
    print(f"Error processing file: {e}")
