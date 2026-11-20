import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory and create if it doesn't exist
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
# The file is a CSV. Based on preview, headers are 'A Raman Shift (cm-1)' and 'B Intensity (a.u.)'
# We assume standard comma-separated CSV unless specified otherwise in preview text, 
# but the preview mentions "one CSV export uses semicolons and decimal commas" as a general note.
# Let's try reading with default settings first. If that fails, we might need sep=';'.
# Given the header format 'A ...', it looks like Excel exported columns labeled A, B.
file_path = "data/raman/R2-260617-1.csv"

try:
    df = pd.read_csv(file_path)
except Exception:
    # Fallback to semicolon separated just in case
    df = pd.read_csv(file_path, sep=';', decimal=',')

# Clean column names to make them easier to use
df.columns = [col.strip() for col in df.columns]

# Identify the shift and intensity columns based on the preview description
# Preview: 'A Raman Shift (cm-1)' | 'B Intensity (a.u.)'
shift_col = None
intensity_col = None

for col in df.columns:
    if "Raman Shift" in col or "Shift" in col:
        shift_col = col
    elif "Intensity" in col:
        intensity_col = col

if shift_col is None or intensity_col is None:
    raise ValueError("Could not find Raman Shift or Intensity columns")

# Filter for 1000-3000 cm^-1 range (though the data seems to already be in this range)
mask = (df[shift_col] >= 1000) & (df[shift_col] <= 3000)
df_plot = df[mask].copy()

# Create the plot
fig, ax = plt.subplots(figsize=(3.5, 2.5)) # Adjusted height for better aspect ratio typically used in papers

# Plot spectrum
ax.plot(df_plot[shift_col], df_plot[intensity_col], color='black', linewidth=1.2)

# Add vertical dashed lines and labels for D, G, 2D bands
bands = {
    "D": 1350,
    "G": 1580,
    "2D": 2690
}

for label, pos in bands.items():
    # Draw vertical line
    ax.axvline(x=pos, color='red', linestyle='--', linewidth=0.8)
    
    # Determine y position for the label. 
    # To avoid overlapping with the curve, we can place it near the top of the axis.
    # Get current ylims
    ymin, ymax = ax.get_ylim()
    y_pos = ymax * 0.9  # Place at 90% of the height
    
    # Add text label
    ax.text(pos + 20, y_pos, label, fontsize=10, color='red', va='center', ha='left')

# Set labels and title
ax.set_xlabel("Raman Shift (cm$^{-1}$)", fontsize=10)
ax.set_ylabel("Intensity (a.u.)", fontsize=10)
ax.set_xlim(1000, 3000)
ax.tick_params(axis='both', which='major', labelsize=8)

# Remove top and right spines for cleaner look (common in publications)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Save as TIFF at 600 dpi
output_filename = os.path.join(OUT_DIR, "R2-260617-1_spectrum.tiff")
plt.tight_layout()
plt.savefig(output_filename, dpi=600, format='tiff')

# Do not call plt.show()
plt.close(fig)
