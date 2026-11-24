import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error loading file: {e}")
    exit()

# Filter for R3 reactor only
df_r3 = df[df['반응기'] == 'R3'].copy()

# Ensure correct data types
# The date column might be string or datetime, we want it sorted and used for x-axis
if not pd.api.types.is_datetime64_any_dtype(df_r3['일자']):
    df_r3['일자'] = pd.to_datetime(df_r3['일자'])

# Create the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Scatter plot: x = 일자 (Date), y = H2/C2H4비, colored by 근무조
# We need to distinguish between '주간' (Day) and '야간' (Night)
colors = {'주간': '#FF69B4', '야간': '#00FFFF'} # HotPink and Cyan for visibility
markers = {'주간': 'o', '야간': 's'}

for shift in ['주간', '야간']:
    subset = df_r3[df_r3['근무조'] == shift]
    if not subset.empty:
        ax.scatter(subset['일자'], subset['H2/C2H4비'], 
                   label=shift, 
                   color=colors[shift], 
                   marker=markers[shift], 
                   alpha=0.7, 
                   edgecolors='k', 
                   linewidths=0.5,
                   s=50)

# Formatting
ax.set_title("R3 반응기: 일자별 H2/C2H4 비율 분포 (근무조별)", fontsize=14)
ax.set_xlabel("일자", fontsize=12)
ax.set_ylabel("H2/C2H4 비", fontsize=12)
ax.legend(title="근무조", loc='best')
ax.grid(True, linestyle='--', alpha=0.6)

# Rotate x-axis labels for better readability of dates
plt.xticks(rotation=45)
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "r3_scatter_date_vs_h2_c2h4_ratio_by_shift.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()

print(f"Plot saved to {output_filename}")
