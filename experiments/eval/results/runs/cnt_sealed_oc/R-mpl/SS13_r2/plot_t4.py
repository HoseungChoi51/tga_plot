import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t4"
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

# Use np.digitize for left-closed bins [edge_i, edge_i+1)
bins_indices = np.digitize(df_valid['X'], bins=bin_edges, right=False) - 1

# Handle values outside the range
valid_bin_mask = (bins_indices >= 0) & (bins_indices < len(bin_edges) - 1)
df_valid['Bin'] = np.where(valid_bin_mask, bins_indices, -1)

# Filter out rows with invalid bin assignments
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
        
        # Plot the line
        plt.plot(subset_sorted['Midpoint'], subset_sorted['Mean_Y'], 
                 marker='o', linestyle='-', color=color, label=label)
        
        # Find the row with the highest mean yield
        max_idx = subset_sorted['Mean_Y'].idxmax()
        max_row = subset_sorted.loc[max_idx]
        
        # Mark the point with a star
        plt.scatter(max_row['Midpoint'], max_row['Mean_Y'], 
                    marker='*', s=200, color='black', zorder=5, edgecolors='white', linewidths=0.5)
        
        # Label the x value of the peak bin
        # Adjust position slightly above the star
        plt.text(max_row['Midpoint'], max_row['Mean_Y'] + 0.5, 
                 f"{max_row['Midpoint']:.2f}", 
                 ha='center', va='bottom', fontsize=9, color='black',
                 bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.8))

# Add labels and title
plt.xlabel('체류시간 Bin Midpoint (s)', fontsize=12)
plt.ylabel('Mean CNT수율 (g/g-cat)', fontsize=12)
plt.title('Binned Mean CNT수율 vs 체류시간 (n>=10, Peak Labeled)', fontsize=14)
plt.legend(loc='best')
plt.grid(True, linestyle='--', alpha=0.7)

# Save the plot
output_file = os.path.join(OUT_DIR, 'binned_mean_yield_vs_residence_time_peak.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
