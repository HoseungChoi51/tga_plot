import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the Raman data file
file_path = "data/raman/R4-260407-1.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# The columns are 'Raman Shift (cm-1)' and 'Intensity (a.u.)' based on preview
x_col = 'Raman Shift (cm-1)'
y_col = 'Intensity (a.u.)'

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(df[x_col], df[y_col], color='blue', linewidth=1.5)

# Add labels and title
plt.xlabel(x_col, fontsize=12)
plt.ylabel(y_col, fontsize=12)
plt.title("Raman Spectrum of Sample R4-260407-1", fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)

# Save the figure
output_filename = os.path.join(OUT_DIR, "raman_R4-260407-1.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
