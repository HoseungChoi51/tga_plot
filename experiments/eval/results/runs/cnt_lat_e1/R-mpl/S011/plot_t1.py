import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to handle potential whitespace or hidden characters
df.columns = df.columns.str.strip()

# Ensure date column is datetime
# The error suggests the header row might be included in the data or there's a specific format issue.
# Based on preview: B 일자 (yyyy-mm-dd) [날짜 ...]
# It seems '일자' contains actual dates but maybe some rows have issues or the column name parsing needs care.
# Let's try to coerce errors to NaT and drop them if necessary, or check if the first row is a unit row.
# Preview says: "some sheets have a units row under the header". 
# If row 0 is units, we should skip it or handle it.
# However, standard read_excel usually handles headers correctly. 
# The error "Unknown datetime string format... yyyy-mm-dd" implies that the string literal "yyyy-mm-dd" was found in the data.
# This strongly suggests that the second row (index 0 after header) contains the unit/format description instead of data.
# Let's inspect by reading without assuming clean data first, or just skipping the potential unit row.

# Strategy: Read with header=0, then check if the first value in '일자' looks like a format string.
# Or simply use `pd.to_datetime` with `errors='coerce'` to turn bad entries into NaT, then drop NaTs.

if '일자' in df.columns:
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')
    # Drop rows where date parsing failed (likely the unit row if present)
    df = df.dropna(subset=['일자'])

# Extract month for grouping
df['월'] = df['일자'].dt.month

# Calculate monthly production per reactor
# Total production (kg) = 생산속도 (g/h) * 가동시간 (h) / 1000
# Check for exact column names after stripping
prod_speed_col = None
run_time_col = None

for col in df.columns:
    if '생산속도' in col:
        prod_speed_col = col
    if '가동시간' in col:
        run_time_col = col

if prod_speed_col and run_time_col:
    df['생산량_kg'] = df[prod_speed_col] * df[run_time_col] / 1000
else:
    raise ValueError("Could not find production speed or run time columns")

# Group by Month and Reactor to sum production
monthly_reactor_prod = df.groupby(['월', '반응기'])['생산량_kg'].sum().unstack(fill_value=0)

# Sort reactors R1-R4
reactors = ['R1', 'R2', 'R3', 'R4']
# Ensure all reactors are present in columns, fill missing with 0
for r in reactors:
    if r not in monthly_reactor_prod.columns:
        monthly_reactor_prod[r] = 0
        
monthly_reactor_prod = monthly_reactor_prod[reactors]

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Create stacked bar chart
bottom = None
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # Standard colors for R1-R4

months_str = [str(m) for m in monthly_reactor_prod.index]

for i, reactor in enumerate(reactors):
    ax.bar(months_str, 
           monthly_reactor_prod[reactor], 
           bottom=bottom, 
           label=reactor, 
           color=colors[i])
    if bottom is None:
        bottom = monthly_reactor_prod[reactor].values.copy()
    else:
        bottom += monthly_reactor_prod[reactor].values

# Labels and Title
ax.set_xlabel('월')
ax.set_ylabel('누적 생산량 (kg)')
ax.set_title('월별 반응기별 누적 생산량')

# Legend outside right
ax.legend(title='반응기', bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent legend cutoff
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "monthly_production_by_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
