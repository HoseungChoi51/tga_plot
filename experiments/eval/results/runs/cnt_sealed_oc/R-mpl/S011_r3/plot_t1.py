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
sheet_name = "런로그"

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    print(f"Error reading file: {e}")
    # If exit() was the issue in some environments, we might just return or handle it differently, 
    # but typically script execution stops. The user said "ran but saved no figure", implying it didn't crash with an error message visible or it crashed silently?
    # Actually, if it ran and saved nothing, maybe the column names were slightly different or logic failed before savefig.
    # Let's ensure we don't use exit() which might behave unexpectedly in some notebook/script contexts without showing the error clearly if captured.
    raise e

# Ensure '일자' is datetime type for month extraction
if '일자' not in df.columns:
    raise ValueError("Column '일자' not found")
    
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# Create a new column for Month (YYYY-MM format)
df['월'] = df['일자'].dt.to_period('M').astype(str)

# Calculate estimated production per run in kg
# Check column existence carefully
rate_col = '생산속도 (g/h)'
time_col = '가동시간 (h)'

if rate_col not in df.columns or time_col not in df.columns:
    raise ValueError(f"Columns '{rate_col}' or '{time_col}' not found. Available: {df.columns.tolist()}")

df['추정_생산량_kg'] = (df[rate_col] * df[time_col]) / 1000

# Group by Month and Reactor, sum the estimated production
# Fill NaNs in groupby result if any reactor missing in a month with 0
monthly_reactor_production = df.groupby(['월', '반응기'])['추정_생산량_kg'].sum().unstack(fill_value=0)

# Sort months chronologically
monthly_reactor_production = monthly_reactor_production.sort_index()

# Get unique reactors sorted (R1, R2, R3, R4)
reactors = sorted(monthly_reactor_production.columns.tolist())

# Plotting
fig, ax = plt.subplots(figsize=(12, 7))

bottom = None
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] 

x_labels = monthly_reactor_production.index.astype(str).tolist()

for i, reactor in enumerate(reactors):
    color = colors[i % len(colors)]
    vals = monthly_reactor_production[reactor].values
    
    if bottom is None:
        bottom = vals.copy()
        bars = ax.bar(x_labels, vals, label=reactor, color=color, edgecolor='white')
    else:
        bars = ax.bar(x_labels, vals, bottom=bottom, label=reactor, color=color, edgecolor='white')
        bottom += vals

# Labels and Title
ax.set_xlabel('월', fontsize=12)
ax.set_ylabel('누적 생산량 (kg)', fontsize=12)
ax.set_title('반응기별 월별 누적 생산량', fontsize=14)

# Legend outside plot area on the right
ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), title='반응기')

# Grid
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Adjust layout to prevent legend cutoff
plt.tight_layout(rect=[0, 0, 0.85, 1]) 

# Save figure
output_file = os.path.join(OUT_DIR, "monthly_production_by_reactor_cumulative.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_file}")

plt.close()
