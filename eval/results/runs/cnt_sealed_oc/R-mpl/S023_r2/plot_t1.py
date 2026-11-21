import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Read data
file_path = 'data/run_log.xlsx'
sheet_name = '런로그'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean column names to handle potential whitespace or formatting issues in headers
df.columns = df.columns.str.strip()

# Find the grade column dynamically since the exact header string caused a KeyError previously
grade_col = None
for col in df.columns:
    if '등급' in str(col):
        grade_col = col
        break

if grade_col is None:
    raise ValueError("Could not find the grade column containing '등급'.")

# Filter out Grade C runs
df_filtered = df[df[grade_col] != 'C'].copy()

# Identify X and Y columns similarly
metal_col = None
igid_col = None
for col in df_filtered.columns:
    if '잔류금속' in str(col):
        metal_col = col
    if 'IG/ID' in str(col) or 'IG_ID' in str(col):
        igid_col = col

if metal_col is None or igid_col is None:
    raise ValueError(f"Could not find required columns. Metal: {metal_col}, IG/ID: {igid_col}")

# Extract relevant columns for regression and force them to numeric types to avoid isnan errors on non-numeric data
x_data = pd.to_numeric(df_filtered[metal_col], errors='coerce')
y_data = pd.to_numeric(df_filtered[igid_col], errors='coerce')

# Remove rows with NaN values in either x or y to ensure valid regression
valid_mask = ~np.isnan(x_data) & ~np.isnan(y_data)
x_clean = x_data[valid_mask]
y_clean = y_data[valid_mask]

# Perform linear regression
slope, intercept = np.polyfit(x_clean, y_clean, 1)

# Calculate R-squared
correlation_matrix = np.corrcoef(x_clean, y_clean)
correlation_xy = correlation_matrix[0, 1]
r_squared = correlation_xy**2

# Generate line points for plotting the regression line
x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
y_line = slope * x_line + intercept

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Scatter plot of filtered data
ax.scatter(x_clean, y_clean, alpha=0.6, edgecolors='k', s=50, label='Data (Grade A/B)')

# Regression line
ax.plot(x_line, y_line, color='red', linestyle='--', linewidth=2, label=f'Regression Line')

# Add text with equation and R^2
eq_text = f'y = {slope:.4f}x + {intercept:.4f}\n$R^2$ = {r_squared:.4f}'
ax.text(0.05, 0.95, eq_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

# Labels and Title
ax.set_xlabel('잔류금속 (wt%)', fontsize=14)
ax.set_ylabel('IG/ID', fontsize=14)
ax.set_title('잔류금속 vs IG/ID 산점도 (등급 C 제외)', fontsize=16)

# Grid and Legend
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right')

# Save figure
output_filename = os.path.join(OUT_DIR, 'scatter_residual_metal_vs_igid.png')
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
