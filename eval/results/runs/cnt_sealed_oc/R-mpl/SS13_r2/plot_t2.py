import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t2"
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

# Convert numeric columns to ensure they are float/int and not objects due to mixed types/NaNs
x_data = pd.to_numeric(df[col_x], errors='coerce')
y_data = pd.to_numeric(df[col_y], errors='coerce')
lot_data = df[col_lot].astype(str).str.strip() # Ensure lot is string for comparison

# Drop rows where x or y is NaN (invalid numeric data)
mask_valid = ~(x_data.isna() | y_data.isna())

# Create a new DataFrame with only valid rows to keep indices aligned
df_valid = df[mask_valid].copy()
x_plot = x_data[mask_valid]
y_plot = y_data[mask_valid]
lot_plot = lot_data[mask_valid]

# Define groups
old_lots = ['FC-2602', 'FC-2603', 'FC-2604', 'FC-2605']
new_lots = ['FC-2606', 'FC-2607', 'FC-2608']

# Create group labels based on the valid lot data
def get_group(lot):
    if lot in old_lots:
        return 'Old Lot (FC-2602~05)'
    elif lot in new_lots:
        return 'New Lot (FC-2606~08)'
    else:
        return 'Other'

group_labels = lot_plot.apply(get_group)

# Plotting
plt.figure(figsize=(10, 6))

colors = {'Old Lot (FC-2602~05)': 'blue', 'New Lot (FC-2606~08)': 'red', 'Other': 'gray'}

# Group by label and plot using boolean masks created from the aligned series
for label, color in colors.items():
    mask = (group_labels == label)
    if mask.any():
        # Use .values to avoid index alignment issues during plotting
        plt.scatter(x_plot[mask.values], y_plot[mask.values], 
                    alpha=0.6, 
                    edgecolors='k', 
                    linewidths=0.5, 
                    label=label, 
                    color=color)

# Add labels and title
plt.xlabel(col_x, fontsize=12)
plt.ylabel(col_y, fontsize=12)
plt.title('Scatter Plot: 체류시간 vs CNT수율 (Color by Catalyst Lot Group)', fontsize=14)
plt.legend(loc='best')

# Save the plot
output_file = os.path.join(OUT_DIR, 'scatter_residence_time_vs_yield_colored.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
