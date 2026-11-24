import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load the data from the specific sheet
file_path = "data/run_log.xlsx"
df_weekly = pd.read_excel(file_path, sheet_name="주간요약")

# Ensure columns are treated correctly
# Column A: 주차, Column G: 총생산량(kg)
x = df_weekly["주차"]
y = df_weekly["총생산량(kg)"]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the line graph for total production per week
ax.plot(x, y, marker='o', linestyle='-', color='blue', label='주간 총생산량')

# Add the target line (red dashed) at 17 kg
target_value = 17
ax.axhline(y=target_value, color='red', linestyle='--', linewidth=2, label=f'주간 목표 ({target_value} kg)')

# Set titles and labels
ax.set_title("주차별 CNT 총생산량 추이", fontsize=14)
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("총생산량 (kg)", fontsize=12)

# Add legend
ax.legend()

# Grid for better readability
ax.grid(True, linestyle=':', alpha=0.6)

# Save the figure
output_file = os.path.join(OUT_DIR, "weekly_production_trend.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close(fig)
