import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/15_r3/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on typical TGA structure or use first few numeric columns
    # From preview: B=Temperature, C=Weight(%), D=D.W(%/C)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    cols = df.columns.tolist()
    for col in cols:
        if 'temperature' in str(col).lower():
            temp_col = col
        elif 'weight' in str(col).lower() and '%' in str(col):
            weight_col = col
        elif 'd.w' in str(col).lower() or 'dtg' in str(col).lower():
            dtg_col = col
            
    if temp_col is None and len(cols) >= 2:
        temp_col = cols[1] # Assuming second column is temperature based on preview
    if weight_col is None and len(cols) >= 3:
        weight_col = cols[2]
        
    color = colors[i % len(colors)]
    
    # Plot Weight (%) on primary y-axis (left)
    line1 = ax1.plot(df[temp_col], df[weight_col], label=f'{sheet_name} - Weight', color=color, linestyle='-')
    
    # Create secondary y-axis for DTG
    ax2 = ax1.twinx()
    if dtg_col is not None:
        line2 = ax2.plot(df[temp_col], df[dtg_col], label=f'{sheet_name} - DTG', color=color, linestyle='--', alpha=0.7)
    else:
        line2 = []
        
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', fontsize=12)
    ax2.set_ylabel('DTG (%/°C)', fontsize=12)
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=9)

ax1.grid(True, linestyle=':', alpha=0.6)
ax1.tick_params(axis='y', labelcolor='#1f77b4') # Color left axis ticks to match first plot? Maybe too complex. Keep default.

plt.title('TGA Curves Comparison', fontsize=14)
plt.tight_layout()

output_path = os.path.join(OUT_DIR, "tga_combined.png")
plt.savefig(output_path, dpi=300)
plt.close()
