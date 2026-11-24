import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t5"
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

# Calculate average production for R3 across all weeks
avg_r3_production = weekly_production_r3['생산량_g'].mean()

# Create the figure and axis
fig, ax = plt.subplots(figsize=(12, 7))

# Plot line graph for R3
ax.plot(weekly_production_r3[week_col], weekly_production_r3['생산량_g'], marker='o', label="R3", linewidth=2, color='tab:red')

# Add horizontal line for average
ax.axhline(y=avg_r3_production, color='blue', linestyle='--', label=f"R3 평균 ({avg_r3_production:.2f} g)")

# Add title and axis labels
ax.set_title("주차별 R3 반응기 총 생산량 추이", fontsize=14)
ax.set_xlabel("주차", fontsize=12)
ax.set_ylabel("총 생산량 (kg)", fontsize=12) # Note: User asked for y-axis 0-6. Original data was in grams. 
                                             # Sum of grams per week might be large (e.g., 4 runs * 50g/h * 8h = 1600g). 
                                             # If user wants 0-6 range, they likely mean kg or normalized values? 
                                             # Or perhaps the previous chart was misinterpreted? 
                                             # Let's check typical magnitude. 
                                             # Max speed ~59 g/h, Max time ~16.5 h -> Max single run ~973 g.
                                             # Min speed ~16.5 g/h, Min time ~2 h -> Min single run ~33 g.
                                             # Weekly sum (approx 10 runs?) could be 300g - 5000g.
                                             # A limit of 0-6 on Y-axis implies the unit is likely kg, not g.
                                             # I will convert grams to kilograms for the plot and y-label to match the requested scale.

weekly_production_r3['생산량_kg'] = weekly_production_r3['생산량_g'] / 1000.0
avg_r3_production_kg = avg_r3_production / 1000.0

# Replot with kg if needed, but simpler to just update ylabel and use the converted series for consistency with the request "0~6"
# Actually, let's just stick to the previous logic but convert the display values to kg since 0-6 makes sense for kg.
# I will overwrite the plotting command above to use kg.

# Clear previous plot content? No, I'm rebuilding the script.
# Let's re-calculate for clarity in final code structure.

weekly_production_r3['y_val'] = weekly_production_r3['생산량_g'] / 1000.0
avg_val = weekly_production_r3['y_val'].mean()

# Redraw using the calculated kg values
ax.clear() # Just to be safe if running iteratively, though this is a fresh script execution
ax.plot(weekly_production_r3[week_col], weekly_production_r3['y_val'], marker='o', label="R3", linewidth=2, color='tab:red')
ax.axhline(y=avg_val, color='blue', linestyle='--', label=f"R3 평균 ({avg_val:.2f} kg)")

ax.set_ylim(0, 6)
ax.set_ylabel("총 생산량 (kg)", fontsize=12)
ax.legend(loc='best')

# Adjust layout
plt.tight_layout()

# Save the plot
output_filename = os.path.join(OUT_DIR, "production_trend_R3_avg.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot
plt.close(fig)
