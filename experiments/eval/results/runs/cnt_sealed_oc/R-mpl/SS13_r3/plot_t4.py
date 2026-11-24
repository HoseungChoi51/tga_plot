import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns containing the keywords to handle potential whitespace or encoding differences
col_residence = None
col_yield = None
col_lot = None

for col in df.columns:
    if '체류시간' in str(col):
        col_residence = col
    if 'CNT수율' in str(col) or ('수율' in str(col) and 'g/g-cat' in str(col)):
        col_yield = col
    if '촉매로트' in str(col) or 'catalyst lot' in str(col).lower():
        col_lot = col

if col_residence is None or col_yield is None or col_lot is None:
    raise ValueError("Could not find required columns for residence time, yield, or catalyst lot.")

# Extract required columns and convert to numeric where appropriate
x_data = pd.to_numeric(df[col_residence], errors='coerce')
y_data = pd.to_numeric(df[col_yield], errors='coerce')
lot_data = df[col_lot].astype(str)

# Create groups: Old (FC-2602 to FC-2605), New (FC-2606 to FC-2608)
def get_group(lot):
    try:
        num_part = lot.split('-')[1]
        num = int(num_part)
        if 2602 <= num <= 2605:
            return 'Old (FC-2602~2605)'
        elif 2606 <= num <= 2608:
            return 'New (FC-2606~2608)'
        else:
            return 'Other'
    except Exception:
        return 'Other'

groups = lot_data.apply(get_group)

# Filter out rows with invalid numeric data or unknown groups
mask = x_data.notna() & y_data.notna() & (groups != 'Other')

df_clean = pd.DataFrame({
    'residence': x_data[mask],
    'yield': y_data[mask],
    'group': groups[mask]
})

# Define bins: 2.5 to 6.75 with width 0.25, left-closed
bin_edges = np.arange(2.5, 6.75 + 0.25, 0.25)
# Use pd.cut to assign bins. right=False means left-closed [edge_i, edge_{i+1})
df_clean['bin'] = pd.cut(df_clean['residence'], bins=bin_edges, right=False)

# Group by bin and group, calculate mean yield and count
grouped = df_clean.groupby(['group', 'bin']).agg(
    mean_yield=('yield', 'mean'),
    count=('yield', 'size')
).reset_index()

# Drop bins with n < 10
grouped_filtered = grouped[grouped['count'] >= 10].copy()

# Calculate midpoints for plotting
grouped_filtered['midpoint'] = grouped_filtered['bin'].apply(lambda x: x.mid)

# Plotting
plt.figure(figsize=(10, 7))

colors = {'Old (FC-2602~2605)': '#1f77b4', 'New (FC-2606~2608)': '#ff7f0e'}
markers = {'Old (FC-2602~2605)': 'o', 'New (FC-2606~2608)': 's'}

for group_name in ['Old (FC-2602~2605)', 'New (FC-2606~2608)']:
    subset = grouped_filtered[grouped_filtered['group'] == group_name]
    if not subset.empty:
        # Sort by midpoint just in case
        subset = subset.sort_values('midpoint')
        
        # Plot the line
        plt.plot(subset['midpoint'], subset['mean_yield'], 
                 marker=markers[group_name], 
                 color=colors[group_name], 
                 linestyle='-', 
                 linewidth=2, 
                 markersize=8,
                 label=group_name)
        
        # Find the bin with the highest mean
        max_idx = subset['mean_yield'].idxmax()
        max_row = subset.loc[max_idx]
        
        # Mark it with a larger star
        plt.scatter(max_row['midpoint'], max_row['mean_yield'], 
                    marker='*', s=300, color=colors[group_name], 
                    edgecolors='k', zorder=5, label=f'Max {group_name}')
        
        # Label its x value
        plt.text(max_row['midpoint'], max_row['mean_yield'], 
                 f"{max_row['midpoint']:.2f}", 
                 verticalalignment='bottom', horizontalalignment='center',
                 fontsize=9, fontweight='bold', color=colors[group_name],
                 bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

# Add labels and title
plt.xlabel('체류시간 Bin Midpoint (s)', fontsize=12)
plt.ylabel('Mean CNT수율 (g/g-cat)', fontsize=12)
plt.title('Mean CNT Yield vs Residence Time Bins (n>=10, Max Marked)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title='Catalyst Group')

# Save figure
output_file = os.path.join(OUT_DIR, 'scatter_binned_mean_yield_max_marked.png')
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
