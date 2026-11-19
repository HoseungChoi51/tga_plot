import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B17_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read sheets
sheet_names = ['PE', 'PVC', 'PET']
data_frames = {}
for sheet in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    data_frames[sheet] = df

# Define offsets and colors
offsets = {'PE': 0, 'PVC': 20, 'PET': 40}
colors = {'PE': '#1f77b4', 'PVC': '#ff7f0e', 'PET': '#2ca02c'}

fig, ax = plt.subplots(figsize=(8, 6))

for sheet in sheet_names:
    df = data_frames[sheet]
    x = df['Temperature (°C)']
    y = df['Weight (%)'] + offsets[sheet]
    label = f"{sheet} (+{offsets[sheet]}%)"
    ax.plot(x, y, color=colors[sheet], label=label, linewidth=1.5)

ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (%) / Offset Weight (%)', fontsize=12)
ax.set_title('TGA Curves of Polymers with Vertical Offsets', fontsize=14)
ax.legend(title='Polymer', loc='upper right')
ax.grid(True, linestyle='--', alpha=0.5)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "tga_offset_curves.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
