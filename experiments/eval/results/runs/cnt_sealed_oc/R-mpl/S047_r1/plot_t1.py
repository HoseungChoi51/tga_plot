import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuration
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# File path based on preview
file_path = "data/run_log.xlsx"

# Read the data
df = pd.read_excel(file_path, sheet_name='런로그')

# Handle date parsing robustly
# The error suggests some values might be strings like 'yyyy-mm-dd' or mixed types.
try:
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
except Exception:
    pass

# Drop rows where date parsing failed completely if any
df = df.dropna(subset=['일자'])

# Clean column names to handle potential whitespace issues which caused KeyError
# We strip all string columns headers to ensure exact match
df.columns = df.columns.str.strip()

# Define expected column names after stripping
col_speed = '생산속도 (g/h)'
col_time = '가동시간 (h)'

# Verify if columns exist, otherwise try to find closest matches (fallback for safety)
if col_speed not in df.columns:
    # Attempt to find a column containing '생산속도' and 'g/h'
    candidates = [c for c in df.columns if '생산속도' in str(c)]
    if candidates:
        col_speed = candidates[0]
        
if col_time not in df.columns:
    # Attempt to find a column containing '가동시간' and 'h'
    candidates = [c for c in df.columns if '가동시간' in str(c)]
    if candidates:
        col_time = candidates[0]

# Calculate per-run production in kg
# Formula: 생산속도 (g/h) * 가동시간 (h) / 1000 to convert g to kg
# Ensure numeric conversion just in case
df[col_speed] = pd.to_numeric(df[col_speed], errors='coerce')
df[col_time] = pd.to_numeric(df[col_time], errors='coerce')

df['일별생산량_kg'] = df[col_speed] * df[col_time] / 1000.0

# Drop rows where calculation resulted in NaN due to bad data
df = df.dropna(subset=['일별생산량_kg', '반응기'])

# Sort by date to ensure correct cumulative calculation order
df = df.sort_values('일자')

# Group by reactor and date to get daily total production per reactor
daily_prod = df.groupby(['반응기', '일자'])['일별생산량_kg'].sum().reset_index()

# Pivot the data so that each reactor is a column
pivot_daily = daily_prod.pivot(index='일자', columns='반응기', values='일별생산량_kg').fillna(0)

# Calculate cumulative production
cumulative_prod = pivot_daily.cumsum()

# Plotting
plt.figure(figsize=(12, 7))

for reactor in cumulative_prod.columns:
    plt.plot(cumulative_prod.index, cumulative_prod[reactor], label=f'{reactor}', linewidth=2)

plt.title('Cumulative Production per Reactor over Date')
plt.xlabel('Date')
plt.ylabel('Cumulative Production (kg)')
plt.legend(title='Reactor')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "cumulative_production_per_reactor.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"Plot saved to {output_filename}")
