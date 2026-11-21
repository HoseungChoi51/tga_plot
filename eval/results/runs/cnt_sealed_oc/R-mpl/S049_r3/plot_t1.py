import pandas as pd
import matplotlib.pyplot as plt
import os

# Set up output directory and font for Korean text
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Helper function to find column by partial match (to handle whitespace or unit variations)
def find_col(df, keyword):
    cols = [c for c in df.columns if keyword in str(c)]
    return cols[0] if cols else None

col_humidity = find_col(df, '외기습도')
col_metal = find_col(df, '잔류금속')
col_date = find_col(df, '일자')

if not col_humidity: raise ValueError("Could not find humidity column")
if not col_metal: raise ValueError("Could not find residual metal column")
if not col_date: raise ValueError("Could not find date column")

# Parse date column
df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
    
# Extract month from date for coloring
df['월'] = df[col_date].dt.month

# Ensure numeric types for plotting columns
df[col_humidity] = pd.to_numeric(df[col_humidity], errors='coerce')
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')

# Drop rows with missing values in relevant columns for clean scatter plot
plot_df = df.dropna(subset=[col_humidity, col_metal, '월'])

# Create the figure
fig, ax = plt.subplots(figsize=(10, 6))

# Get unique months sorted
months = sorted(plot_df['월'].unique())
# Define distinct colors for each month (3-8)
# Using a colormap to distinguish them clearly
colors = plt.cm.viridis([i/(len(months)-1) for i in range(len(months))])

for i, month in enumerate(months):
    subset = plot_df[plot_df['월'] == month]
    ax.scatter(
        subset[col_humidity], 
        subset[col_metal], 
        color=colors[i], 
        label=f'{month}월', 
        alpha=0.7, 
        edgecolors='w', 
        linewidth=0.5
    )

# Formatting labels and title
ax.set_xlabel(col_humidity, fontsize=12)
ax.set_ylabel(col_metal, fontsize=12)
ax.set_title('외기습도 vs 잔류금속 산점도 (월별 색상 구분)', fontsize=14)
ax.legend(title='캘린더 월', loc='best')
ax.grid(True, linestyle='--', alpha=0.5)

# Save the plot
output_file = os.path.join(OUT_DIR, 'scatter_humidity_residual_metal.png')
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
