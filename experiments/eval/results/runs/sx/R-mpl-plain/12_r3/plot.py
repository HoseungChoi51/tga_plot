import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/12_r3/out"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read all sheets
xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

fig, axes = plt.subplots(len(sheet_names), 1, figsize=(8, 4 * len(sheet_names)), sharex=True)

if len(sheet_names) == 1:
    axes = [axes]

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Identify columns based on the preview structure
    # Assuming column order: Time, Temperature, Weight(%), D.W(%/C)
    temp_col = df.columns[1]
    weight_col = df.columns[2]
    dtg_col = df.columns[3]
    
    ax = axes[i]
    color_main = colors[i % len(colors)]
    
    # Plot TGA (Weight %) on primary axis
    line1, = ax.plot(df[temp_col], df[weight_col], label='TGA (Weight %)', color=color_main, linewidth=2)
    ax.set_ylabel('Weight (%)')
    ax.tick_params(axis='y', labelcolor=color_main)
    
    # Create secondary axis for DTG
    ax2 = ax.twinx()
    line2, = ax2.plot(df[temp_col], df[dtg_col], label='DTG (%/°C)', color='gray', linestyle='--', linewidth=1.5)
    ax2.set_ylabel('DTG (%/°C)')
    
    # Add vertical line at 450 °C
    ax.axvline(x=450, color='red', linestyle=':', linewidth=1.5, label='450 °C')
    
    # Add text annotation
    # Find a suitable y-position for the text to avoid overlapping with data if possible
    # For simplicity, placing it near the top of the plot area relative to the TGA curve
    max_weight = df[weight_col].max()
    min_weight = df[weight_col].min()
    y_pos = min_weight + (max_weight - min_weight) * 0.8
    
    ax.text(450, y_pos, '산화 시작', rotation=90, va='center', ha='right', fontsize=10, color='red')
    
    # Combine legends
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    # Add custom handle for the vertical line if needed, but usually just labeling the line object is enough if we added a label to axvline
    # Since axvline returns a Line2D object, we can capture it. Let's adjust slightly.
    
    # Re-doing legend handling properly
    vline = ax.axvline(x=450, color='red', linestyle=':', linewidth=1.5)
    lines.append(vline)
    labels.append('450 °C')
    
    ax.legend(lines, labels, loc='upper right', bbox_to_anchor=(1.1, 1.1))
    
    ax.set_title(f'{sheet_name}')
    ax.grid(True, linestyle='--', alpha=0.6)

axes[-1].set_xlabel('Temperature (°C)')

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
