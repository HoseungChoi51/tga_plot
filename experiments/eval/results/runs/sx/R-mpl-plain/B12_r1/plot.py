import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure fonts for Korean support if needed, though labels are English here mostly except maybe title? 
# User request is in English, but system prompt mentions Korean users. Let's stick to English labels as per data headers unless specified otherwise.
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B12_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
df = pd.read_csv(DATA_FILE)

# Extract relevant columns based on preview
# Col B: Temperature (°C), Col C: Weight (%)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"

# Filter data for x range 100 to 900
mask = (df[temp_col] >= 100) & (df[temp_col] <= 900)
df_filtered = df[mask]

# Create plot
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(df_filtered[temp_col], df_filtered[weight_col], label='Weight', color='blue')

# Set axis limits and labels
ax.set_xlim(100, 900)
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Weight (%)')
ax.set_title('TGA Weight Curve')
ax.grid(True, linestyle='--', alpha=0.7)

# Find residue at 900 °C
# We look for the point closest to 900 °C in the original or filtered data
# Since we filtered up to 900, the last point in filtered should be close.
# Let's find the specific value at exactly 900 if possible, or nearest.
df_900 = df[df[temp_col] == 900]
if not df_900.empty:
    residue_weight = df_900.iloc[0][weight_col]
else:
    # Nearest
    idx = (df[temp_col] - 900).abs().idxmin()
    residue_weight = df.loc[idx, weight_col]

# Annotate residue
ax.annotate(f'Residue: {residue_weight:.2f}%',
            xy=(900, residue_weight),
            xytext=(750, residue_weight + 5),
            arrowprops=dict(facecolor='black', shrink=0.05),
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="k", lw=1, alpha=0.8))

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "tga_weight_curve.png")
plt.savefig(output_path, dpi=300)
plt.close()
