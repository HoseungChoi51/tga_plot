import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns for production rate and time
col_rate = '생산속도 (g/h)'
col_time = '가동시간 (h)'
col_reactor = '반응기'
col_date = '일자'

# Check if columns exist
if col_rate not in df_runs.columns or col_time not in df_runs.columns:
    cols = df_runs.columns.tolist()
    rate_col = [c for c in cols if '생산속도' in str(c)]
    time_col = [c for c in cols if '가동시간' in str(c)]
    if rate_col and time_col:
        col_rate = rate_col[0]
        col_time = time_col[0]
    else:
        raise ValueError(f"Could not find required columns. Available: {cols}")

# Clean numeric columns: convert to numeric, coercing errors to NaN then dropping them later or filling 0
# The error suggests strings are present. We force conversion.
df_runs[col_rate] = pd.to_numeric(df_runs[col_rate], errors='coerce')
df_runs[col_time] = pd.to_numeric(df_runs[col_time], errors='coerce')

# Drop rows where critical numeric data is missing after conversion
df_clean = df_runs.dropna(subset=[col_rate, col_time, col_reactor, col_date]).copy()

# Calculate total production per run in kg
# Production (kg) = Rate (g/h) * Time (h) / 1000
df_clean['Run_Production_kg'] = (df_clean[col_rate] * df_clean[col_time]) / 1000.0

# Extract Month from Date
# Ensure date column is datetime
df_clean['Date'] = pd.to_datetime(df_clean[col_date], errors='coerce')
df_clean = df_clean.dropna(subset=['Date'])
df_clean['Month'] = df_clean['Date'].dt.month

# Group by Month and Reactor to sum production
pivot_table = df_clean.pivot_table(index='Month', columns=col_reactor, values='Run_Production_kg', aggfunc='sum')

# Ensure all reactors R1-R4 are present as columns, fill NaN with 0
reactors = ['R1', 'R2', 'R3', 'R4']
for r in reactors:
    if r not in pivot_table.columns:
        pivot_table[r] = 0

# Sort columns to ensure consistent stacking order
pivot_table = pivot_table[reactors].fillna(0)

# Create Plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot stacked bar chart
bottom = np.zeros(len(pivot_table))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] 

x_labels = [str(m) + '월' for m in pivot_table.index]

for i, reactor in enumerate(reactors):
    bars = ax.bar(x_labels, pivot_table[reactor], bottom=bottom, label=reactor, color=colors[i])
    bottom += pivot_table[reactor].values

# Labels and Title
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('생산량 (kg)', fontsize=12)
ax.set_title('월별 반응기별 누적 생산량', fontsize=14)
ax.tick_params(axis='both', which='major', labelsize=10)

# Legend outside right
ax.legend(title='반응기', bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent clipping of legend
plt.tight_layout()

# Save figure
out_dir = "out"
os.makedirs(out_dir, exist_ok=True)
save_path = os.path.join(out_dir, "monthly_production_by_reactor.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')

plt.close()
print(f"Plot saved to {save_path}")
