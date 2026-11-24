import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and file paths
OUT_DIR = "out/t1"
DATA_FILE = "data/run_log.xlsx"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the '런로그' sheet from the Excel file
try:
    df = pd.read_excel(DATA_FILE, sheet_name='런로그')
except Exception as e:
    print(f"Error reading file: {e}")
    raise e

# Print available columns to debug potential naming mismatches (e.g., full-width spaces vs half-width, etc.)
print("Available columns:", list(df.columns))

# Strategy: Normalize column names by removing all whitespace characters (including full-width space U+3000)
# This handles cases where headers might have inconsistent spacing.
def normalize_col_name(name):
    if isinstance(name, str):
        # Replace common whitespace chars with empty string for matching
        return name.replace(' ', '').replace('\u3000', '').strip()
    return str(name)

df['col_norm'] = [normalize_col_name(c) for c in df.columns]

# Target normalized names based on request:
# '체류시간 (s)' -> '체류시간(s)'
# 'CNT수율 (g/g-cat)' -> 'CNT수율(g/g-cat)'
# '반응기' -> '반응기'

target_cols_map = {}
for orig_col in df.columns:
    norm_col = normalize_col_name(orig_col)
    if norm_col == '체류시간(s)':
        target_cols_map[orig_col] = '체류시간 (s)'
    elif norm_col == 'CNT수율(g/g-cat)':
        target_cols_map[orig_col] = 'CNT수율 (g/g-cat)'
    elif norm_col == '반응기':
        target_cols_map[orig_col] = '반응기'

# Rename columns in the dataframe to standard expected names if found
if target_cols_map:
    df.rename(columns=target_cols_map, inplace=False) 
    # Note: Inplace is deprecated, so we assign back or use rename without inplace? 
    # Actually df.rename returns a new DF if inplace=False. Let's do that safely.
    df = df.rename(columns=target_cols_map)
    
    # Drop the helper column
    if 'col_norm' in df.columns:
        df.drop(columns=['col_norm'], inplace=True)

# Verify required columns exist now
required_cols = ['체류시간 (s)', '반응기', 'CNT수율 (g/g-cat)']
missing_cols = [c for c in required_cols if c not in df.columns]

if missing_cols:
    print(f"Still missing after normalization: {missing_cols}")
    print(f"Current columns: {list(df.columns)}")
    raise ValueError(f"Required columns not found: {missing_cols}")

# Clean data: drop rows with NaN in critical columns
df_clean = df.dropna(subset=required_cols).copy()

# Convert numeric types explicitly just in case
df_clean['체류시간 (s)'] = pd.to_numeric(df_clean['체류시간 (s)'], errors='coerce')
df_clean['CNT수율 (g/g-cat)'] = pd.to_numeric(df_clean['CNT수율 (g/g-cat)'], errors='coerce')

# Drop any remaining NaNs after conversion
df_clean = df_clean.dropna(subset=['체류시간 (s)', 'CNT수율 (g/g-cat)'])

# Define bin edges: 2.5 to 7.0 with step 0.5
# Bins: [2.5, 3.0), [3.0, 3.5), ..., [6.5, 7.0)
# Request says "left-closed", which corresponds to right=False in pd.cut
bin_edges = np.arange(2.5, 7.1, 0.5)
bin_labels = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(len(bin_edges)-1)]

# Create a new column for bins using pd.cut
df_clean['체류시간_빈'] = pd.cut(
    df_clean['체류시간 (s)'], 
    bins=bin_edges, 
    labels=bin_labels, 
    right=False 
)

# Check if we have valid data for pivoting
valid_data = df_clean[df_clean['체류시간_빈'].notna()]

if valid_data.empty:
    print("No valid data to plot.")
else:
    # Pivot table: Index = Bin Labels (Rows), Columns = Reactors, Values = Mean CNT Yield
    pivot_table = valid_data.pivot_table(
        index='체류시간_빈', 
        columns='반응기', 
        values='CNT수율 (g/g-cat)', 
        aggfunc='mean'
    )
    
    # Reorder columns to ensure R1-R4 order if present
    reactor_order = ['R1', 'R2', 'R3', 'R4']
    existing_reactors = [r for r in reactor_order if r in pivot_table.columns]
    other_reactors = [c for c in pivot_table.columns if c not in reactor_order]
    pivot_table = pivot_table[existing_reactors + other_reactors]
    
    # Sort index by the numeric start of the label to ensure correct order
    ordered_bins = [label for label in bin_labels if label in pivot_table.index]
    pivot_table = pivot_table.reindex(ordered_bins)

    # Plotting the heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Use imshow for heatmap
    im = ax.imshow(pivot_table.values, cmap='YlGnBu', aspect='auto')
    
    # Set ticks and labels
    ax.set_xticks(np.arange(len(pivot_table.columns)))
    ax.set_yticks(np.arange(len(pivot_table.index)))
    ax.set_xticklabels(pivot_table.columns)
    ax.set_yticklabels(pivot_table.index)
    
    # Rotate x-axis labels if needed
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('평균 CNT 수율 (g/g-cat)', rotation=-90, va="bottom")
    
    # Annotate cells with values
    vmin = np.nanmin(pivot_table.values)
    vmax = np.nanmax(pivot_table.values)
    mid = (vmin + vmax) / 2
    
    for i in range(len(pivot_table.index)):
        for j in range(len(pivot_table.columns)):
            val = pivot_table.iloc[i, j]
            if not pd.isna(val):
                text = f"{val:.2f}"
                color = "white" if val > mid else "black"
                ax.text(j, i, text, ha="center", va="center", color=color)
    
    # Titles and labels
    ax.set_title('체류시간 빈별 반응기별 평균 CNT 수율', fontsize=14, pad=20)
    ax.set_xlabel('반응기', fontsize=12)
    ax.set_ylabel('체류시간 (s)', fontsize=12)
    
    plt.tight_layout()
    
    # Save figure
    save_path = os.path.join(OUT_DIR, "heatmap_yield_by_residence_time_and_reactor.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Heatmap saved to {save_path}")
