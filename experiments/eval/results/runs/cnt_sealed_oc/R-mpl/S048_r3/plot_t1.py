import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data from Excel file
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Filter for Reactor R3 only
df_r3 = df[df["반응기"] == "R3"].copy()

# Create scatter plot: 일자 vs H2/C2H4비, colored by 근무조
plt.figure(figsize=(12, 6))

# Map colors to 근무조 values (assuming '주간' and '야간')
colors = {'주간': '#1f77b4', '야간': '#ff7f0e'}

for shift in ['주간', '야간']:
    subset = df_r3[df_r3["근무조"] == shift]
    plt.scatter(subset["일자"], subset["H2/C2H4비"], 
                color=colors[shift], label=shift, alpha=0.7, edgecolors='w', s=50)

plt.title("R3 반응기: 일자별 H2/C2H4 비 산점도")
plt.xlabel("일자")
plt.ylabel("H2/C2H4 비")
plt.legend(title="근무조")
plt.grid(True, linestyle='--', alpha=0.6)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)
plt.tight_layout()

# Save the figure
output_file = os.path.join(OUT_DIR, "R3_H2C2H4_ratio_by_date.png")
plt.savefig(output_file, dpi=300)
plt.close()
