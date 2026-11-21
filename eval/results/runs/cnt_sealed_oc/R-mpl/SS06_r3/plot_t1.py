import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory and ensure it exists
OUT_DIR = "out/t1"
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

# Loop through each file, read the data, and plot
for path in file_paths:
    # Extract label from filename (e.g., R1-260326-1)
    label = os.path.splitext(os.path.basename(path))[0]
    
    # Read CSV assuming standard comma delimiter based on preview info structure
    # The preview indicates headers 'Raman Shift (cm-1)' and 'Intensity (a.u.)'
    df = pd.read_csv(path)
    
    # Identify columns dynamically or use expected names
    # Based on preview: A is Raman Shift, B is Intensity
    x_col = df.columns[0]
    y_col = df.columns[1]
    
    # Plot
    ax.plot(df[x_col], df[y_col], label=label, linewidth=1.5, alpha=0.8)

# Add labels, title, legend, and grid
ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
ax.set_ylabel("Intensity (a.u.)", fontsize=12)
ax.set_title("Overlaid Raman Spectra from CNT Production Runs", fontsize=14)
ax.legend(title="Sample ID", loc="best", fontsize=9)
ax.grid(True, linestyle='--', alpha=0.6)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "raman_spectra_overlay.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_filename}")

# Close the plot to free memory
plt.close(fig)
