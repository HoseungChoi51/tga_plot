import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory and create if it doesn't exist
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
sheet_name = "주간요약"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error reading file: {e}")
    raise

# Ensure '주차' is sorted for correct plotting order
df = df.sort_values(by='주차')

# Extract columns needed for plotting
weeks = df['주차']
total_production = df['총생산량(kg)']
target_line = 17

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the line graph for weekly total production
ax.plot(weeks, total_production, marker='o', linestyle='-', color='steelblue', label='주별 총생산량')

# Add the target line (red dashed)
ax.axhline(y=target_line, color='red', linestyle='--', linewidth=2, label=f'목표 ({target_line} kg)')

# Set titles and labels
ax.set_title('주차별 총생산량 추이', fontsize=14)
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('총생산량 (kg)', fontsize=12)

# Add legend
ax.legend()

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "weekly_total_production.png")
plt.savefig(output_filename, dpi=300)

# Close the plot to free memory
plt.close(fig)

print(f"Plot saved to {output_filename}")
