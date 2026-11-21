import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/21_r2/out"

# Read data, skipping the first 8 rows as indicated by header_rows=8 and data_start_row=9
df = pd.read_excel(DATA_FILE, sheet_name='Sheet1', skiprows=8)

# Extract columns based on user request: C -> X, D -> Y1, E -> Y2
# In the preview, Column B is Time, C is Temperature, D is Weight(%), E is D.W(%/C)
# User asks for "C행" (Column C content) as X, "D행" as Y1, "E행" as Y2.
# Based on standard Excel column mapping in the preview:
# Col C name is "Temperature", Col D name is "Weight(%)", Col E name is "D.W(%/C)"

x_col = df.columns[0] # This corresponds to Column B (Time) if read directly? 
# Wait, the preview says:
# Col B: Time
# Col C: Temperature
# Col D: Weight(%)
# Col E: D.W(%/C)
# The dataframe read with skiprows=8 will have headers from row 9.
# Let's check the actual column names in the dataframe.

# Assuming the dataframe columns are named according to the header row found at row 9.
# The preview lists them as: "Time", "Temperature", "Weight(%)", "D.W(%/C)" corresponding to B, C, D, E.
# So df columns should be ['Time', 'Temperature', 'Weight(%)', 'D.W(%/C)'] or similar.

# Identify columns by name to be safe, falling back to index if names are weird.
col_names = df.columns.tolist()

# Try to find the specific columns requested:
# X-axis: Column C content -> "Temperature"
# Y1-axis: Column D content -> "Weight(%)"
# Y2-axis: Column E content -> "D.W(%/C)"

try:
    x_data = df['Temperature']
    y1_data = df['Weight(%)']
    y2_data = df['D.W(%/C)']
except KeyError:
    # Fallback to positional indices if names don't match exactly
    # Index 0: Time (B), 1: Temperature (C), 2: Weight (D), 3: D.W (E)
    x_data = df.iloc[:, 1]
    y1_data = df.iloc[:, 2]
    y2_data = df.iloc[:, 3]

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Y1 (Weight %)
color1 = 'tab:red'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.plot(x_data, y1_data, color=color1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# Create second axis sharing the same X-axis
ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('D.W (%/°C)', color=color2, fontsize=12)
ax2.plot(x_data, y2_data, color=color2, linestyle='--', label='D.W (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# Add titles and legends
plt.title('TGA Analysis: Weight and Derivative Weight vs Temperature', fontsize=14)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

# Adjust layout to prevent clipping
fig.tight_layout()

# Save the plot
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
