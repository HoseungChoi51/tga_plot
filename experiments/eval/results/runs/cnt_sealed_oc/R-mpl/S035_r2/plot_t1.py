import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Extract unique temperature values to assign colors
unique_temps = sorted(df['2존온도(°C)'].unique())

# Create a figure and axis
fig, ax = plt.subplots(figsize=(10, 7))

# Plot scatter points for each temperature group with different colors
for temp in unique_temps:
    subset = df[df['2존온도(°C)'] == temp]
    ax.scatter(subset['수율(g/g-cat)'], 
               subset['순도(%)'], 
               label=f"{temp} °C", 
               s=50, 
               alpha=0.8, 
               edgecolors='w', 
               linewidth=0.5)

# Add labels and title
ax.set_xlabel('수율 (g/g-cat)', fontsize=12)
ax.set_ylabel('순도 (%)', fontsize=12)
ax.set_title('DOE 데이터: 수율 vs 순도 (2존 온도별 색상 구분)', fontsize=14)

# Add legend
ax.legend(title='2존 온도', bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent clipping of legend
plt.tight_layout()

# Save the plot
output_path = os.path.join(OUT_DIR, "doe_yield_vs_purity.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')

# Close the plot
plt.close()
