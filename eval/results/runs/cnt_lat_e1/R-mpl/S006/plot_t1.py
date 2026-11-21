import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the '주간요약' sheet from the Excel file
file_path = "data/run_log.xlsx"
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# Extract relevant columns: 주차 (Week) and 총생산량(kg) (Total Production kg)
# Ensure numeric types for plotting
df_weekly['주차'] = pd.to_numeric(df_weekly['주차'], errors='coerce')
df_weekly['총생산량(kg)'] = pd.to_numeric(df_weekly['총생산량(kg)'], errors='coerce')

# Drop rows with NaN in critical columns just in case
df_plot = df_weekly.dropna(subset=['주차', '총생산량(kg)'])

# Create the plot
fig, ax = plt.subplots(figsize=(12, 6))

# Plot the line graph for weekly total production
ax.plot(df_plot['주차'], df_plot['총생산량(kg)'], marker='o', linestyle='-', color='blue', label='주간 총생산량')

# Add the target line at 17 kg as a red dashed line
target_value = 17
ax.axhline(y=target_value, color='red', linestyle='--', linewidth=1.5, label=f'목표 ({target_value} kg)')

# Set labels and title
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('총생산량 (kg)', fontsize=12)
ax.set_title('주차별 총생산량 추이', fontsize=14)

# Add legend
ax.legend(loc='best')

# Add grid for better readability
ax.grid(True, linestyle=':', alpha=0.6)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "weekly_production_trend.png")
plt.savefig(output_filename, dpi=300)
plt.close()
