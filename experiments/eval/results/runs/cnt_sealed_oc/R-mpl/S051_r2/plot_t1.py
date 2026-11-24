import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data from Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Clean column names to remove potential whitespace or special characters that might cause KeyError
# The error suggests the columns with spaces/units were not found exactly as expected.
# Let's inspect and strip all columns just in case.
df.columns = df.columns.str.strip()

# Identify the correct column names based on the preview provided:
# N 체류시간 (s), Q CNT수율 (g/g-cat), P 가동시간 (h)
# We will use these exact strings after stripping whitespace.

col_residence = '체류시간 (s)'
col_yield = 'CNT수율 (g/g-cat)'
col_runtime = '가동시간 (h)'
col_week = '주차'
col_reactor = '반응기'

# Ensure these columns exist; if not, try to find close matches (defensive programming)
for col in [col_residence, col_yield, col_runtime, col_week, col_reactor]:
    if col not in df.columns:
        # Attempt to find a column that starts with the same base name
        candidates = [c for c in df.columns if str(c).startswith(col.split()[0])]
        if candidates:
            globals()[f'actual_{col.split()[0]}'] = candidates[0]
        else:
            raise ValueError(f"Column '{col}' not found in dataframe.")

# Re-assign actual column variables if they were corrected above (simplified logic for this specific script)
# Assuming standard headers based on preview, let's explicitly map them again if needed.
# The previous error was likely due to invisible unicode chars or strict matching failure. 
# Using .str.strip() usually fixes it. If keys still fail, we can use iloc or index by position if known, 
# but here we rely on the cleaned string match.

# Convert types where necessary
df[col_week] = pd.to_numeric(df[col_week], errors='coerce')
df[col_residence] = pd.to_numeric(df[col_residence], errors='coerce')
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')
df[col_runtime] = pd.to_numeric(df[col_runtime], errors='coerce')

# Filter data: 주차 14-26 and 반응기 in {R1, R2}
mask_week = (df[col_week] >= 14) & (df[col_week] <= 26)
mask_reactor = df[col_reactor].isin(['R1', 'R2'])
filtered_df = df[mask_week & mask_reactor]

# Drop rows where critical plotting columns are NaN
filtered_df = filtered_df.dropna(subset=[col_residence, col_yield, col_runtime])

# Check if filtered data exists
if filtered_df.empty:
    print("No data found after filtering.")
else:
    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 7))
    
    reactors = ['R1', 'R2']
    colors = {'R1': '#1f77b4', 'R2': '#ff7f0e'}
    
    for r in reactors:
        subset = filtered_df[filtered_df[col_reactor] == r]
        if not subset.empty:
            # Marker size proportional to 가동시간 (runtime)
            marker_sizes = subset[col_runtime] * 50
            
            ax.scatter(
                subset[col_residence], 
                subset[col_yield],
                s=marker_sizes,
                color=colors[r],
                alpha=0.7,
                edgecolors='k',
                linewidth=0.5,
                label=f'{r}'
            )
            
    # Labels and Title
    ax.set_xlabel('체류시간 (s)', fontsize=12)
    ax.set_ylabel('CNT수율 (g/g-cat)', fontsize=12)
    ax.set_title('주차 14–26, R1/R2: 체류시간 vs CNT수율\n(Marker Size ∝ 가동시간)', fontsize=14)
    
    # Grid and Legend
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(title='반응기', loc='best')
    
    # Save figure
    output_file = os.path.join(OUT_DIR, "scatter_residence_yield.png")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close(fig)
    print(f"Plot saved to {output_file}")
