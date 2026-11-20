import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define paths and output directory
DATA_FILE = "data/raman/R2-260617-1.csv"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data
# The file is a CSV with two columns: Raman Shift (cm-1) and Intensity (a.u.)
# Headers are in English based on preview, but we handle them robustly.
df = pd.read_csv(DATA_FILE)

# Ensure column names are clean if they have spaces or special chars from Excel export issues
# Based on preview: 'A Raman Shift (cm-1)' | 'B Intensity (a.u.)' 
# But usually pandas reads first row as header. Let's check typical structure.
# If the first row is header:
cols = df.columns.tolist()
if len(cols) >= 2:
    x_col = cols[0]
    y_col = cols[1]
else:
    raise ValueError("Data file must have at least 2 columns")

x_data = df[x_col]
y_data = df[y_col]

# Create figure
fig, ax = plt.subplots(figsize=(3.5, 2.5)) # Adjusted height for aspect ratio

# Plot spectrum
ax.plot(x_data, y_data, color='black', linewidth=1.2)

# Define peak positions and labels
peaks = {
    1350: 'D',
    1580: 'G',
    2690: '2D'
}

# Add vertical dotted lines and labels
for pos, label in peaks.items():
    # Draw vertical line
    ax.axvline(x=pos, color='red', linestyle=':', linewidth=1.0)
    
    # Find the y-position for the text label to avoid overlap with the curve if possible
    # Simple approach: place it near the top of the plot area relative to local max or just high enough
    # Get local intensity around the peak to position label above
    mask = (x_data > pos - 50) & (x_data < pos + 50)
    if not mask.empty:
        local_max_y = y_data[mask].max()
    else:
        local_max_y = y_data.max() * 0.8
        
    # Place text slightly above the line start or use axis fraction for consistency
    # Using axis coordinates for Y placement ensures they don't hide behind tall peaks unexpectedly
    # Or simply place them at a fixed high Y value
    y_text_pos = y_data.max() * 0.95
    
    ax.text(pos, y_text_pos, label, ha='center', va='bottom', fontsize=10, fontweight='bold')

# Formatting for paper quality
ax.set_xlabel('Raman Shift (cm⁻¹)', fontsize=10)
ax.set_ylabel('Intensity (a.u.)', fontsize=10)
ax.tick_params(axis='both', which='major', labelsize=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Tight layout
plt.tight_layout()

# Save as TIFF 600 dpi
output_path = os.path.join(OUT_DIR, "R2-260617-1_spectrum.tiff")
fig.savefig(output_path, format='tiff', dpi=600)

plt.close(fig)
print(f"Plot saved to {output_path}")
