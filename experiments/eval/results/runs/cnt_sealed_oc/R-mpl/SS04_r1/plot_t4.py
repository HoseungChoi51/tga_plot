import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# Load the run log data from Excel
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify column names for throughput and time
col_speed = [c for c in df.columns if '생산속도' in str(c)]
col_time = [c for c in df.columns if '가동시간' in str(c)]
col_reactor = [c for c in df.columns if '반응기' in str(c)]
col_week = [c for c in df.columns if '주차' in str(c)]

if not col_speed:
    raise ValueError("Column for production speed (생산속도) not found.")
if not col_time:
    raise ValueError("Column for operation time (가동시간) not found.")
if not col_reactor:
    raise ValueError("Column for reactor (반응기) not found.")
if not col_week:
    raise ValueError("Column for week (주차) not found.")

speed_col = col_speed[0]
time_col = col_time[0]
reactor_col = col_reactor[0]
week_col = col_week[0]

# Convert relevant columns to numeric
df[speed_col] = pd.to_numeric(df[speed_col], errors='coerce')
df[time_col] = pd.to_numeric(df[time_col], errors='coerce')
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

# Drop rows where conversion failed
valid_mask = ~df[speed_col].isna() & ~df[time_col].isna() & ~df[week_col].isna()
df_valid = df[valid_mask].copy()

# Calculate production amount for each run: 생산속도 (g/h) * 가동시간 (h)
df_valid['생산량_g'] = df_valid[speed_col] * df_valid[time_col]

# Filter for R3 only
df_r3 = df_valid[df_valid[reactor_col] == 'R3']

# Group by Week to get total production per week for R3
weekly_production_r3 = df_r3.groupby(week_col)['생산량_g'].sum().reset_index()

# Sort by week index to ensure correct order for plotting
weekly_production_r3 = weekly_production_r3.sort_values(by=week_col)

# Create the figure and axis
fig, ax = plt.subplots(figsize=(12, 7))

# Plot line graph for R3
ax.plot(weekly_production_r3[week_col], weekly_production_r3['생산량_g'], marker='o', label="R3", linewidth=2, color='tab:red')

# Add title and axis labels
ax.set_title("주차별 R3 반응기 총 생산량 추이", fontsize=14)
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("총 생산량 (g)", fontsize=12)

# Add legend
ax.legend(loc='best')

# Adjust layout
plt.tight_layout()

# Save the plot
output_filename = os.path.join(OUT_DIR, "production_trend_R3.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot to prevent showing it in interactive environments if requested not to show
plt.close(fig)
