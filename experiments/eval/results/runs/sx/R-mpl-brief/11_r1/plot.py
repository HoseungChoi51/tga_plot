import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/11_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    
    # Identify columns based on preview info
    # Time, Temperature, Weight(%), D.W(%/C)
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
    
    # Check if columns exist, otherwise try to find them by index or partial name
    if x_col not in df.columns:
        # Fallback logic if names differ slightly
        cols = df.columns.tolist()
        for c in cols:
            if 'temp' in c.lower(): x_col = c
            elif 'weight' in c.lower() and '%' in c: y1_col = c
            elif 'd.w' in c.lower() or 'dtg' in c.lower(): y2_col = c
            
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (y1)
    line1 = ax1.plot(df[x_col], df[y1_col], color='#1f4e9c', label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f4e9c')
    
    # Plot DTG (y2) - multiplied by -1 to point peaks up
    ax2 = ax1.twinx()
    dtg_data = df[y2_col] * -1
    line2 = ax2.plot(df[x_col], dtg_data, color='#c0392b', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    
    # Title is sheet name
    ax1.set_title(sheet, fontsize=14)
    
    # Residue Label (at nearest 800°C)
    # Find the row closest to 800°C
    idx_800 = (df[x_col] - 800).abs().idxmin()
    residue_val = df.loc[idx_800, y1_col]
    temp_residue = df.loc[idx_800, x_col]
    
    # Draw marker for residue
    ax1.scatter([temp_residue], [residue_val], color='#1f4e9c', zorder=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(temp_residue, residue_val), 
                 xytext=(10, -15), textcoords='offset points',
                 ha='left', va='top', color='#1f4e9c', fontsize=10,
                 arrowprops=dict(arrowstyle='->', color='#1f4e9c'))
    
    # Peak Label: User requested to remove peak display ("피크 표시 지워줘")
    # So we skip drawing the peak annotation and marker.
    
    # Legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5))
    
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet]).strip()
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
