import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load the run log data from Excel
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify column names for throughput and time
# The preview shows headers like '생산속도 (g/h)' but actual file might have slight variations or spaces.
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

# Sort reactors alphabetically if needed
total_production_by_reactor = total_production_by_reactor.sort_values(by=reactor_col)

# Prepare labels and values for the pie chart
labels = total_production_by_reactor[reactor_col]
values = total_production_by_reactor['생산량_g']

# Create the figure and axis
fig, ax = plt.subplots(figsize=(8, 8))

# Plot the pie chart
wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel1.colors)

# Add title
ax.set_title("반응기별 총 생산량 비중", fontsize=14)

# Equal aspect ratio ensures that pie is drawn as a circle.
ax.axis('equal')

# Save the plot
output_filename = os.path.join(OUT_DIR, "production_share_by_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot to prevent showing it in interactive environments if requested not to show
plt.close(fig)
