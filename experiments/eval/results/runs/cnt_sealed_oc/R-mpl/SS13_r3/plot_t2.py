import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t2"
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
    # Extract numbers from strings like FC-2602
    try:
        # Assuming format FC-XXXX
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

# Filter out rows with invalid numeric data or unknown groups if desired, but here we plot valid ones
mask = x_data.notna() & y_data.notna() & (groups != 'Other')

x_clean = x_data[mask]
y_clean = y_data[mask]
g_clean = groups[mask]

# Plotting
plt.figure(figsize=(10, 7))

colors = {'Old (FC-2602~2605)': '#1f77b4', 'New (FC-2606~2608)': '#ff7f0e'}

for group_name, color in colors.items():
    idx = g_clean == group_name
    if any(idx):
        plt.scatter(x_clean[idx], y_clean[idx], 
                    alpha=0.6, 
                    edgecolors='k', 
                    s=50, 
                    label=group_name,
                    color=color)

# Add labels and title
plt.xlabel('체류시간 (s)', fontsize=12)
plt.ylabel('CNT수율 (g/g-cat)', fontsize=12)
plt.title('Scatter Plot: 체류시간 vs CNT수율 (Color by Catalyst Lot Group)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title='Catalyst Group')

# Save figure
output_file = os.path.join(OUT_DIR, 'scatter_residence_time_vs_yield_colored.png')
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
