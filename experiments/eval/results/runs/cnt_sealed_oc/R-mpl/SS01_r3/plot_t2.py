import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Load the '주간요약' sheet from the Excel file
file_path = "data/run_log.xlsx"
df_summary = pd.read_excel(file_path, sheet_name="주간요약")

# Extract data for plotting
weeks = df_summary['주차']
total_production = df_summary['총생산량(kg)']

# Create the plot
plt.figure(figsize=(12, 6))

# Define colors: skyblue for weeks < 14, orange for weeks >= 14
colors = ['skyblue' if w < 14 else 'orange' for w in weeks]

bars = plt.bar(weeks, total_production, color=colors, edgecolor='black')

# Add labels and title
plt.xlabel('주차 (Week)', fontsize=12)
plt.ylabel('총생산량 (kg)', fontsize=12)
plt.title('주차별 총생산량 (Weekly Total Production)', fontsize=14)

# Add grid lines for better readability
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Save the figure
output_file = os.path.join(OUT_DIR, "weekly_total_production.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
