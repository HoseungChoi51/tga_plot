import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to remove potential whitespace issues from Excel headers
df.columns = df.columns.str.strip()

# Identify the correct columns by matching keywords
x_col_candidates = [col for col in df.columns if '산화개시온도' in str(col)]
y_col_candidates = [col for col in df.columns if '잔류금속' in str(col)]
grade_col_candidates = [col for col in df.columns if '등급' in str(col)]

if not x_col_candidates or not y_col_candidates or not grade_col_candidates:
    raise ValueError("Could not find required columns: 산화개시온도, 잔류금속, or 등급")

x_col = x_col_candidates[0]
y_col = y_col_candidates[0]
grade_col = grade_col_candidates[0]

# Ensure numeric types
df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

# Drop rows with missing values in these columns
plot_df = df.dropna(subset=[x_col, y_col, grade_col])

# Filter out Grade C
filtered_df = plot_df[plot_df[grade_col] != 'C']

# Define colors for grades (A and B only now)
color_map = {
    'A': 'green',
    'B': 'orange'
}

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Plot each grade separately for legend and color
for grade, color in color_map.items():
    subset = filtered_df[filtered_df[grade_col] == grade]
    if not subset.empty:
        ax.scatter(subset[x_col], subset[y_col], 
                   alpha=0.6, edgecolors='k', s=50, 
                   label=f'Grade {grade}', color=color)

# Compute linear regression on the filtered data (excluding C)
if len(filtered_df) > 1:
    x_vals = filtered_df[x_col].values
    y_vals = filtered_df[y_col].values
    
    # Calculate slope and intercept using numpy polyfit
    coeffs = np.polyfit(x_vals, y_vals, 1)
    slope, intercept = coeffs
    
    # Calculate R-squared
    predicted_y = slope * x_vals + intercept
    ss_res = np.sum((y_vals - predicted_y)**2)
    ss_tot = np.sum((y_vals - np.mean(y_vals))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Generate line points
    min_x = np.min(x_vals)
    max_x = np.max(x_vals)
    line_x = np.linspace(min_x, max_x, 100)
    line_y = slope * line_x + intercept
    
    # Plot regression line
    ax.plot(line_x, line_y, color='blue', linestyle='--', linewidth=2, label='Linear Fit (excl. C)')
    
    # Add R² text annotation
    ax.text(0.95, 0.05, f'$R^2 = {r_squared:.3f}$', transform=ax.transAxes, 
            fontsize=12, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# Add labels and title
ax.set_xlabel(x_col, fontsize=12)
ax.set_ylabel(y_col, fontsize=12)
ax.set_title("잔류금속 vs 산화개시온도 산점도 (C 제외, 회귀분석 포함)", fontsize=14)

# Add legend
ax.legend(title="등급", loc="best")

# Add grid
ax.grid(True, linestyle='--', alpha=0.7)

# Save figure
output_filename = os.path.join(OUT_DIR, "scatter_residual_metal_vs_onset_temp_no_C.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
