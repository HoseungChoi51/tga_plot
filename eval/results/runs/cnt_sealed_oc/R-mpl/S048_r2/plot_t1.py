import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
sheet_name = '런로그'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Filter for R3 only
df_r3 = df[df['반응기'] == 'R3'].copy()

# Ensure date is datetime for plotting if necessary (matplotlib handles strings usually, but better safe)
# The preview says '일자' is date type in Excel, so pandas should read it as datetime or string. 
# If it's string, we can convert. Let's assume it works directly or convert to be safe.
if not pd.api.types.is_datetime64_any_dtype(df_r3['일자']):
    df_r3['일자'] = pd.to_datetime(df_r3['일자'])

# Create scatter plot
fig, ax = plt.subplots(figsize=(12, 8))

# Define colors for shifts
shift_colors = {'주간': '#1f77b4', '야간': '#ff7f0e'} # Blue for Day, Orange for Night

for shift, color in shift_colors.items():
    subset = df_r3[df_r3['근무조'] == shift]
    ax.scatter(subset['일자'], subset['H2/C2H4비'], 
               label=shift, 
               color=color, 
               alpha=0.6, 
               s=50, 
               edgecolors='w', 
               linewidth=0.5)

ax.set_xlabel('일자')
ax.set_ylabel('H2/C2H4비')
ax.set_title('R3 반응기: 일자별 H2/C2H4 비율 분포 (근무조별 색상 구분)')
ax.legend(title='근무조')
ax.grid(True, linestyle='--', alpha=0.5)

# Format x-axis dates if they are too many ticks
fig.autofmt_xdate(rotation=45)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "r3_scatter_date_vs_h2_c2h4_ratio.png")
plt.savefig(save_path, dpi=300)
plt.close()
