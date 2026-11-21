import pandas as pd
import matplotlib.pyplot as plt
import os

# Setup
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/raman/R2-260617-1.csv"
df = pd.read_csv(file_path)

# Identify columns: A is Raman Shift, B is Intensity based on preview
shift_col = df.columns[0]
intensity_col = df.columns[1]

# Create figure with specified width
fig, ax = plt.subplots(figsize=(3.5, 3.5 * 0.7)) # Assuming a reasonable aspect ratio for height, e.g., square-ish or standard paper column width often has specific height needs, but let's keep it compact. Or just use default height scaling? Let's set figsize to (3.5, 2.5) which is common for single column papers.
fig, ax = plt.subplots(figsize=(3.5, 2.5))

# Plot spectrum
ax.plot(df[shift_col], df[intensity_col], color='black', linewidth=1)

# Add vertical dotted lines and labels for D, G, 2D bands
bands = {
    'D': 1350,
    'G': 1580,
    '2D': 2690
}

for name, pos in bands.items():
    ax.axvline(x=pos, linestyle=':', color='gray', linewidth=1)
    # Position label slightly above the middle of the y-axis range or relative to max intensity
    # Get current ylims to place text nicely
    ymin, ymax = ax.get_ylim()
    ax.text(pos + 20, ymax * 0.9, name, fontsize=8, ha='left', va='top')

# Formatting
ax.set_xlabel('Raman Shift (cm$^{-1}$)', fontsize=9)
ax.set_ylabel('Intensity (a.u.)', fontsize=9)
ax.set_xlim(1000, 3000)
ax.tick_params(labelsize=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Tight layout
plt.tight_layout()

# Save as TIFF at 600 dpi
output_path = os.path.join(OUT_DIR, "R2-260617-1_spectrum.tiff")
plt.savefig(output_path, dpi=600, format='tiff')
plt.close(fig)
