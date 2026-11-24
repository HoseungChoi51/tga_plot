import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t3"
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

# Calculate averages for Week 1-13 and Week 14-26
avg_early = total_production[weeks <= 13].mean()
avg_late = total_production[weeks >= 14].mean()

# Draw horizontal lines for the averages
plt.axhline(y=avg_early, color='green', linestyle='--', linewidth=2, label=f'1~13주 평균 ({avg_early:.2f} kg)')
plt.axhline(y=avg_late, color='red', linestyle='-.', linewidth=2, label=f'14~26주 평균 ({avg_late:.2f} kg)')

# Add labels and title
plt.xlabel('주차 (Week)', fontsize=12)
plt.ylabel('총생산량 (kg)', fontsize=12)
plt.title('주차별 총생산량 및 구간별 평균선', fontsize=14)

# Add legend
plt.legend(loc='upper right')

# Add grid lines for better readability
plt.grid(axis='y', linestyle=':', alpha=0.5)

# Save the figure
output_file = os.path.join(OUT_DIR, "weekly_total_production.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
