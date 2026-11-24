import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory and ensure it exists
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# List of Raman CSV files to plot
file_paths = [
    "data/raman/R1-260326-1.csv",
    "data/raman/R1-260711-1.csv",
    "data/raman/R1-260716-1.csv",
    "data/raman/R2-260616-1.csv",
    "data/raman/R2-260617-1.csv",
    "data/raman/R3-260810-2.csv",
    "data/raman/R4-260407-1.csv",
    "data/raman/R4-260721-1.csv"
]

# Create a new figure and axis
fig, ax = plt.subplots(figsize=(12, 8))

# Loop through each file, read the data, normalize, and plot
for path in file_paths:
    # Extract label from filename (e.g., R1-260326-1)
    label = os.path.splitext(os.path.basename(path))[0]
    
    # Read CSV
    df = pd.read_csv(path)
    
    # Identify columns dynamically
    x_col = df.columns[0]
    y_col = df.columns[1]
    
    # Get raw data arrays
    shift = df[x_col].values
    intensity = df[y_col].values
    
    # Find the maximum intensity within the G-band region (1550-1620 cm⁻¹)
    g_band_mask = (shift >= 1550) & (shift <= 1620)
    if np.any(g_band_mask):
        max_g_intensity = np.max(intensity[g_band_mask])
    else:
        # Fallback if no data points in range (unlikely given description)
        max_g_intensity = np.max(intensity)
        
    # Normalize intensity so that the max in G-band is 1
    if max_g_intensity != 0:
        normalized_intensity = intensity / max_g_intensity
    else:
        normalized_intensity = intensity
        
    # Filter data to show only 1200-1700 cm⁻¹ region
    display_mask = (shift >= 1200) & (shift <= 1700)
    
    # Plot normalized spectra in the specified range
    ax.plot(shift[display_mask], normalized_intensity[display_mask], 
            label=label, linewidth=1.5, alpha=0.8)

# Add labels, title, legend, and grid
ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
ax.set_ylabel("Normalized Intensity (a.u.)", fontsize=12)
ax.set_title("Overlaid Raman Spectra (1200–1700 cm⁻¹)\nNormalized by G-band Max (1550–1620 cm⁻¹)", fontsize=14)
ax.legend(title="Sample ID", loc="best", fontsize=9)
ax.grid(True, linestyle='--', alpha=0.6)

# Set x-axis limits explicitly to ensure focus on the requested region
ax.set_xlim(1200, 1700)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "raman_spectra_normalized.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_filename}")

# Close the plot to free memory
plt.close(fig)
