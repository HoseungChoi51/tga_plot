import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Robustly find columns by substring to handle potential whitespace or header variations
col_x = None
col_y = None
col_lot = None

for c in df.columns:
    if isinstance(c, str):
        if '체류시간' in c:
            col_x = c
        if 'CNT수율' in c:
            col_y = c
        if '촉매로트' in c:
            col_lot = c

if not all([col_x, col_y, col_lot]):
    raise ValueError(f"Could not find required columns. Available: {df.columns.tolist()}")

# Convert numeric columns and ensure lot is string
x_data = pd.to_numeric(df[col_x], errors='coerce')
y_data = pd.to_numeric(df[col_y], errors='coerce')
lot_data = df[col_lot].astype(str).str.strip()

# Filter valid rows (non-NaN x, y, and lot)
mask_valid = ~(x_data.isna() | y_data.isna() | lot_data.isin(['nan', 'NaN', '']))
df_valid = df[mask_valid].copy()
df_valid['X'] = x_data[mask_valid]
df_valid['Y'] = y_data[mask_valid]
df_valid['Lot'] = lot_data[mask_valid]

# Define groups
old_lots = ['FC-2602', 'FC-2603', 'FC-2604', 'FC-2605']
new_lots = ['FC-2606', 'FC-2607', 'FC-2608']

def get_group(lot):
    if lot in old_lots:
        return 'Old Lot (FC-2602~05)'
    elif lot in new_lots:
        return 'New Lot (FC-2606~08)'
    else:
        return 'Other'

df_valid['Group'] = df_valid['Lot'].apply(get_group)

# Binning configuration
bin_edges = np.arange(2.5, 6.75 + 0.25, 0.25) # Generates edges 2.5, 2.75, ..., 6.75

# To achieve left-closed bins [2.5, 2.75), we can manually assign bin indices
# This avoids version-specific keyword arguments for pd.cut
bins_indices = np.digitize(df_valid['X'], bins=bin_edges, right=False) - 1

# Handle values outside the range (e.g., exactly 6.75 or greater, or less than 2.5)
# digitize with right=False returns index of the bin into which each element falls.
# For x in [2.5, 2.75), it returns 1. Subtracting 1 gives 0.
# For x < 2.5, it returns 0 -> index -1 (invalid)
# For x >= 6.75, it returns len(bin_edges) -> index len(bin_edges)-1 (which might be out of bounds if last edge is exclusive?)
# Let's check: 
# If x = 2.5, digitize(..., right=False) returns 1. Index = 0. Correct.
# If x = 6.75, digitize(..., right=False) returns len(bin_edges) (since 6.75 >= 6.75? No, usually strictly greater if right=False logic applies differently).
# Actually, np.digitize(x, bins, right=False) returns index i such that bins[i-1] <= x < bins[i].
# So for x=6.75, since the last bin edge is 6.75, x < 6.75 is false. It will return len(bins).
# We only want bins within [2.5, 6.75). Values >= 6.75 should be excluded or put in a separate overflow bin which we ignore if n<10 anyway.
# Values < 2.5 return 0, so index -1. These are invalid.

valid_bin_mask = (bins_indices >= 0) & (bins_indices < len(bin_edges) - 1)
df_valid['Bin'] = np.where(valid_bin_mask, bins_indices, -1)

# Filter out rows with invalid bin assignments (outside 2.5-6.75 range)
df_binned = df_valid[df_valid['Bin'] != -1].copy()

# Calculate bin midpoints for plotting
midpoints = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]

# Group by Group and Bin to calculate mean Y and count N
grouped = df_binned.groupby(['Group', 'Bin']).agg(
    Mean_Y=('Y', 'mean'),
    Count=('Y', 'size')
).reset_index()

# Drop bins with n < 10
grouped_filtered = grouped[grouped['Count'] >= 10].copy()

# Map Bin index to Midpoint
grouped_filtered['Midpoint'] = grouped_filtered['Bin'].apply(lambda b: midpoints[int(b)])

# Plotting
plt.figure(figsize=(10, 6))

colors = {'Old Lot (FC-2602~05)': 'blue', 'New Lot (FC-2606~08)': 'red', 'Other': 'gray'}

for label, color in colors.items():
    subset = grouped_filtered[grouped_filtered['Group'] == label]
    if not subset.empty:
        # Sort by midpoint just in case
        subset_sorted = subset.sort_values('Midpoint')
        plt.plot(subset_sorted['Midpoint'], subset_sorted['Mean_Y'], 
                 marker='o', linestyle='-', color=color, label=label)

# Add labels and title
plt.xlabel('체류시간 Bin Midpoint (s)', fontsize=12)
plt.ylabel('Mean CNT수율 (g/g-cat)', fontsize=12)
plt.title('Binned Mean CNT수율 vs 체류시간 (n>=10)', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)

# Save the plot
output_file = os.path.join(OUT_DIR, 'binned_mean_yield_vs_residence_time.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
