import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Configure Korean font support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B06_r2/out"

# Ensure output directory exists
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read the data file
# The preview indicates it's a text file with header in row 1 (index 0 if 0-based for pandas skiprows logic depends on structure)
# Preview says: header_rows: [1], data_start_row: 2. 
# In pandas, if the first line is metadata or empty, we might need to adjust. 
# Usually, "header_rows: [1]" in these previews means the column names are in the 1st physical line of the file content provided.
# Let's try reading it directly. If there are extra lines at the top, we might need to inspect.
# Based on typical TGA exports and the preview showing columns starting immediately, let's assume standard CSV-like or whitespace separated.
try:
    # Try reading as whitespace-separated or tab-separated first, often used in .txt TGA files
    df = pd.read_csv(DATA_FILE, sep='\s+', encoding='utf-8', engine='python')
except Exception:
    # Fallback to comma or other separators if whitespace fails
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8')
    except Exception:
        # Last resort: read all lines and find the header manually
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the line containing 'Time' or similar headers
        header_idx = -1
        for i, line in enumerate(lines):
            if 'Time' in line or 'Temperature' in line or 'Weight' in line:
                header_idx = i
                break
        
        if header_idx != -1:
            from io import StringIO
            clean_data = ''.join(lines[header_idx:])
            df = pd.read_csv(StringIO(clean_data), sep='\s+', engine='python')
        else:
            raise ValueError("Could not identify header in the data file.")

# Identify columns based on the request and preview
# Request: x=Time, y1(left)=Weight, y2(right)=Temperature
# Preview columns: "Time (min)", "Temperature (°C)", "Weight (%)"

col_time = None
col_weight = None
col_temp = None

for col in df.columns:
    c_lower = str(col).lower()
    if 'time' in c_lower:
        col_time = col
    elif 'weight' in c_lower:
        col_weight = col
    elif 'temperature' in c_lower or 'temp' in c_lower:
        col_temp = col

if not all([col_time, col_weight, col_temp]):
    raise ValueError(f"Could not identify required columns. Found: {df.columns.tolist()}")

# Extract data
x = df[col_time].values
y1 = df[col_weight].values
y2 = df[col_temp].values

# Create the plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight on left axis (y1)
color_left = '#1f4e9c'
ax1.set_xlabel('시간 (분)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color_left, fontsize=12)
line1, = ax1.plot(x, y1, color=color_left, linewidth=2, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color_left)

# Create shared x-axis, secondary y-axis for Temperature
ax2 = ax1.twinx()
color_right = '#c0392b'
ax2.set_ylabel('온도 (°C)', color=color_right, fontsize=12)
line2, = ax2.plot(x, y2, color=color_right, linewidth=2, linestyle='--', label='온도 (°C)')
ax2.tick_params(axis='y', labelcolor=color_right)

# Title
ax1.set_title('Isothermal Analysis', fontsize=14, fontweight='bold')

# Combine legends
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5), fontsize=10)

# Add grid
ax1.grid(True, linestyle=':', alpha=0.6)

# Mark the weight at 140 minutes
target_time = 140.0
# Find the index closest to 140 min
idx = np.argmin(np.abs(x - target_time))
val_x = x[idx]
val_y1 = y1[idx]

# Draw marker and annotation
ax1.scatter(val_x, val_y1, color='green', s=50, zorder=5)
annotation_text = f'{val_y1:.2f}%'
ax1.annotate(annotation_text,
             xy=(val_x, val_y1),
             xytext=(10, 10),
             textcoords='offset points',
             fontsize=10,
             color='black',
             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2', color='gray'))

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = Path(OUT_DIR) / "isothermal_plot.png"
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
