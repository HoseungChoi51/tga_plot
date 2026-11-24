import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Load the run log data from Excel
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify column names for throughput and time
col_speed = [c for c in df.columns if '생산속도' in str(c)]
col_time = [c for c in df.columns if '가동시간' in str(c)]
col_reactor = [c for c in df.columns if '반응기' in str(c)]

if not col_speed:
    raise ValueError("Column for production speed (생산속도) not found.")
if not col_time:
    raise ValueError("Column for operation time (가동시간) not found.")
if not col_reactor:
    raise ValueError("Column for reactor (반응기) not found.")

speed_col = col_speed[0]
time_col = col_time[0]
reactor_col = col_reactor[0]

# Convert relevant columns to numeric to handle any non-numeric entries or string representations of numbers
df[speed_col] = pd.to_numeric(df[speed_col], errors='coerce')
df[time_col] = pd.to_numeric(df[time_col], errors='coerce')

# Drop rows where conversion failed (NaN) for these specific calculations
valid_mask = ~df[speed_col].isna() & ~df[time_col].isna()
df_valid = df[valid_mask].copy()

# Calculate production amount for each run: 생산속도 (g/h) * 가동시간 (h)
df_valid['생산량_g'] = df_valid[speed_col] * df_valid[time_col]

# Group by Reactor and sum the production amount
total_production_by_reactor = df_valid.groupby(reactor_col)['생산량_g'].sum().reset_index()

# Sort reactors alphabetically
total_production_by_reactor = total_production_by_reactor.sort_values(by=reactor_col)

# Prepare labels and values for the bar chart
labels = total_production_by_reactor[reactor_col]
values = total_production_by_reactor['생산량_g']

# Create the figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the bar chart
bars = ax.bar(labels, values, color=plt.cm.Pastel1.colors[:len(labels)])

# Add title and axis labels
ax.set_title("반응기별 총 생산량", fontsize=14)
ax.set_xlabel("반응기", fontsize=12)
ax.set_ylabel("총 생산량 (g)", fontsize=12)

# Add value labels on top of bars
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

# Adjust layout
plt.tight_layout()

# Save the plot
output_filename = os.path.join(OUT_DIR, "production_share_by_reactor_bar.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot to prevent showing it in interactive environments if requested not to show
plt.close(fig)
