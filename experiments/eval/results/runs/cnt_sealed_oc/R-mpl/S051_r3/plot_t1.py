import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# The error indicates column name mismatch. 
# Preview shows: N 체류시간 (s), Q CNT수율 (g/g-cat), P 가동시간 (h).
# However, sometimes Excel headers have extra spaces or different formats.
# Let's strip whitespace from all columns to be safe and identify the correct names.
df.columns = df.columns.str.strip()

# Identify columns by partial match if exact fails, but let's try using the likely names first.
# Based on the preview:
# N is '체류시간 (s)' -> might be '체류시간(s)' or similar. 
# Let's create a mapping helper to find columns containing key substrings.

def get_col(df, keyword):
    cols = [c for c in df.columns if keyword in c]
    if not cols:
        raise ValueError(f"Column with keyword '{keyword}' not found. Available: {list(df.columns)}")
    return cols[0]

try:
    col_week = get_col(df, '주차')
    col_reactor = get_col(df, '반응기')
    col_residence = get_col(df, '체류시간')
    col_yield = get_col(df, 'CNT수율')
    col_duration = get_col(df, '가동시간')
except Exception as e:
    print(e)
    # Fallback printing all columns for debugging if needed
    print("Columns:", list(df.columns))
    raise

# Convert relevant columns to numeric where necessary
df[col_week] = pd.to_numeric(df[col_week], errors='coerce')
df[col_residence] = pd.to_numeric(df[col_residence], errors='coerce')
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')
df[col_duration] = pd.to_numeric(df[col_duration], errors='coerce')

# Filter data: 주차 14–26 and 반응기 in {R1, R2}
filtered_df = df[(df[col_week] >= 14) & (df[col_week] <= 26) & (df[col_reactor].isin(['R1', 'R2']))]

# Drop rows with missing values in the relevant columns after conversion
filtered_df = filtered_df.dropna(subset=[col_residence, col_yield, col_duration])

if filtered_df.empty:
    print("No data found after filtering.")
else:
    # Prepare plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Scatter plot
    # x: 체류시간, y: CNT수율
    # marker size proportional to 가동시간. 
    size_factor = 30 
    sizes = filtered_df[col_duration] * size_factor

    scatter = ax.scatter(filtered_df[col_residence], filtered_df[col_yield], s=sizes, alpha=0.6, edgecolors='k', linewidths=0.5, c='steelblue')

    # Labels and Title
    ax.set_xlabel(col_residence, fontsize=12)
    ax.set_ylabel(col_yield, fontsize=12)
    ax.set_title('주차 14–26, R1/R2 반응기: 체류시간 vs CNT수율\n(마커 크기 ∝ 가동시간)', fontsize=14)

    # Add legend for marker size explanation
    min_time = filtered_df[col_duration].min()
    max_time = filtered_df[col_duration].max()
    
    # Create a range of sizes for the legend to show variation
    if min_time == max_time:
        legend_times = [min_time]
    else:
        mid_time = (min_time + max_time) / 2
        legend_times = [min_time, mid_time, max_time]

    proxy_artists = []
    for t in legend_times:
        # Use same styling as scatter
        p = ax.scatter([], [], s=t*size_factor, label=f"{t:.1f} h", alpha=0.6, edgecolors='k', linewidths=0.5, c='steelblue')
        proxy_artists.append(p)

    leg = ax.legend(handles=proxy_artists, title='가동시간 (h)', loc='best', fontsize=10)

    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Save figure
    output_path = os.path.join(OUT_DIR, "scatter_residence_yield_R1R2_week14_26.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
