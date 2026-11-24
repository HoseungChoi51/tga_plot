import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and ensure it exists
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Check if required columns exist (handling potential whitespace in headers)
cols = df.columns.tolist()
col_residual_metal = [c for c in cols if '잔류금속' in str(c)]
col_oxidation_temp = [c for c in cols if '산화개시온도' in str(c)]
col_grade = [c for c in cols if '등급' in str(c)]

if not col_residual_metal or not col_oxidation_temp or not col_grade:
    raise ValueError("Required columns '잔류금속', '산화개시온도', '등급' not found.")

residual_col = col_residual_metal[0]
temp_col = col_oxidation_temp[0]
grade_col = col_grade[0]

# Clean data: convert to numeric and drop NaNs for plotting
df_plot = df[[residual_col, temp_col, grade_col]].copy()
df_plot[residual_col] = pd.to_numeric(df_plot[residual_col], errors='coerce')
df_plot[temp_col] = pd.to_numeric(df_plot[temp_col], errors='coerce')
df_plot.dropna(inplace=True)

# Filter out Grade C
df_filtered = df_plot[df_plot[grade_col] != 'C'].copy()

# Define color mapping for grades (A green, B orange)
color_map = {'A': 'green', 'B': 'orange'}

# Create the scatter plot
fig, ax = plt.subplots(figsize=(10, 7))

# Plot each grade separately
for grade in ['A', 'B']:
    mask = df_filtered[grade_col] == grade
    subset = df_filtered[mask]
    if not subset.empty:
        ax.scatter(subset[residual_col], subset[temp_col], 
                   alpha=0.6, edgecolors='k', s=50, 
                   color=color_map.get(grade, 'gray'), 
                   label=f'Grade {grade}')

# Calculate linear regression for filtered data (A + B)
x = df_filtered[residual_col].values
y = df_filtered[temp_col].values

# Use polyfit for 1st degree polynomial
slope, intercept = np.polyfit(x, y, 1)

# Generate line points for smooth regression line
x_line = np.linspace(min(x), max(x), 100)
y_line = slope * x_line + intercept

ax.plot(x_line, y_line, color='black', linestyle='--', linewidth=2, label='Linear Fit (A+B)')

# Calculate R-squared
y_pred = slope * x + intercept
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

# Add labels and title
ax.set_xlabel(residual_col, fontsize=12)
ax.set_ylabel(temp_col, fontsize=12)
ax.set_title('잔류금속 vs 산화개시온도 산점도 (C등급 제외)', fontsize=14)

# Add text annotation for R²
text_str = f'$R^2 = {r_squared:.3f}$'
ax.text(0.05, 0.95, text_str, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

# Add legend
ax.legend(title='등급', loc='best')

# Add grid for better readability
ax.grid(True, linestyle='--', alpha=0.5)

# Save the figure
output_filename = os.path.join(OUT_DIR, "scatter_residual_metal_vs_oxidation_temp_no_C_with_regression.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
