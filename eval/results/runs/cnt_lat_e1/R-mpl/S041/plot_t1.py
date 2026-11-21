import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Count runs per catalyst lot
lot_counts = df["촉매로트"].value_counts().sort_values()

# Create horizontal bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(lot_counts.index, lot_counts.values, color="steelblue", edgecolor="black")

# Add labels and title
ax.set_xlabel("런 수 (개)", fontsize=12)
ax.set_ylabel("촉매 로트", fontsize=12)
ax.set_title("촉매 로트별 런 수 분포", fontsize=14)

# Add value labels on bars
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
            va='center', ha='left', fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "catalyst_lot_run_count.png")
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()
