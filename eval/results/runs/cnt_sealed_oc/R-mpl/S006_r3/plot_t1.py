import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data from Excel file
file_path = "data/run_log.xlsx"
df_weekly_summary = pd.read_excel(file_path, sheet_name="주간요약")

# Extract relevant columns for plotting
week = df_weekly_summary["주차"]
total_production = df_weekly_summary["총생산량(kg)"]

# Create the plot
fig, ax = plt.subplots(figsize=(12, 6))

# Plot line graph of weekly total production
ax.plot(week, total_production, marker='o', linestyle='-', color='blue', label="총생산량 (kg)")

# Add red dotted target line at 17 kg
ax.axhline(y=17, color='red', linestyle='--', label="주간 목표 (17 kg)")

# Formatting
ax.set_xlabel("주차")
ax.set_ylabel("총생산량 (kg)")
ax.set_title("주차별 총생산량 추이")
ax.legend(loc="best")
ax.grid(True, linestyle="--", alpha=0.5)

# Save figure
output_file = os.path.join(OUT_DIR, "weekly_production_trend.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close(fig)
