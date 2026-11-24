import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read data from Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: strip whitespace to ensure exact matches
df.columns = df.columns.str.strip()

cols = df.columns.tolist()

def find_col(keywords):
    """Find a column name that contains all keywords."""
    for c in cols:
        if all(k in c for k in keywords):
            return c
    return None

col_yield = find_col(['CNT', '수율'])
col_metal = find_col(['잔류', '금속'])
col_lot = '촉매로트'
col_reactor = '반응기'

if col_yield is None or col_metal is None:
    raise ValueError(f"Could not find required columns. Available columns: {cols}")

# Convert numeric columns to float to avoid 'object' dtype errors during aggregation
# Using errors='coerce' turns non-numeric entries into NaN, which mean() handles by skipping them
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')

# Define aggregation groups and metrics using the identified column names
group_cols = [col_lot, col_reactor]
agg_metrics = {
    col_metal: 'mean',
    col_yield: 'mean'
}

# Perform groupby aggregation
grouped_df = df.groupby(group_cols).agg(agg_metrics).reset_index()

# Drop rows where either metric is NaN (resulting from coercion or missing data)
grouped_df = grouped_df.dropna(subset=[col_metal, col_yield])

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Get unique lots for consistent coloring
unique_lots = sorted(grouped_df[col_lot].unique())
colors = plt.cm.tab10(range(len(unique_lots)))

for i, lot in enumerate(unique_lots):
    subset = grouped_df[grouped_df[col_lot] == lot]
    ax.scatter(
        subset[col_metal], 
        subset[col_yield],
        color=colors[i],
        label=lot,
        s=100,
        edgecolors='black',
        linewidths=0.5
    )

# Add legend
ax.legend(title="촉매로트", loc="best")

# Labels and Title
ax.set_xlabel(f'평균 {col_metal}')
ax.set_ylabel(f'평균 {col_yield}')
ax.set_title('촉매로트별 반응기 평균 성능 비교 (잔류금속 vs 수율)')

# Grid for better readability
ax.grid(True, linestyle='--', alpha=0.6)

# Save the figure
output_filename = os.path.join(OUT_DIR, "aggregated_lot_reactor_plot.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)
