import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/18_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets from the Excel file
xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

fig, axes = plt.subplots(len(sheet_names), 1, figsize=(10, 4 * len(sheet_names)), sharex=False)

# Handle case where there is only one sheet (axes would be a single object, not an array)
if len(sheet_names) == 1:
    axes = [axes]

for i, sheet_name in enumerate(sheet_names):
    ax1 = axes[i]
    
    # Read data for the current sheet
    df = pd.read_excel(xl_file, sheet_name=sheet_name)
    
    # Identify columns based on the preview info
    # X: Temperature, Y1: Weight(%), Y2: D.W(%/C)
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
    
    if x_col not in df.columns or y1_col not in df.columns or y2_col not in df.columns:
        # Fallback to positional if names don't match exactly (though they should based on preview)
        # Assuming B=1, C=2, D=3 in 0-indexed terms -> indices 1, 2, 3
        x_col = df.columns[1]
        y1_col = df.columns[2]
        y2_col = df.columns[3]

    temp = df[x_col]
    weight = df[y1_col]
    dtg = df[y2_col]
    
    # Plot TGA curve on primary axis (left)
    line1, = ax1.plot(temp, weight, color='blue', label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=10)
    ax1.set_ylabel('Weight (%)', color='blue', fontsize=10)
    ax1.tick_params(axis='y', labelcolor='blue')
    
    # Set X-axis tick interval to 100
    ax1.set_xticks(range(0, int(max(temp)) + 100, 100))
    
    # Create secondary axis for DTG
    ax2 = ax1.twinx()
    line2, = ax2.plot(temp, dtg, color='red', linestyle='--', label='dW/dT (%/°C)')
    ax2.set_ylabel('dW/dT (%/°C)', color='red', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Set Y2 axis range as requested: -0.05 ~ 1.2
    # Note: The user asked for y2 axis range. In TGA plots, usually DTG is negative for mass loss.
    # The request says "-0.05~1.2". Let's apply this directly to the right axis (ax2).
    ax2.set_ylim(-0.05, 1.2)
    
    # Combine legends
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')
    
    # Title with sheet name
    ax1.set_title(f'TGA Analysis: {sheet_name}', fontsize=12)
    
    # Add grid
    ax1.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_plots.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
