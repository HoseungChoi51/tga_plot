import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Ensure output directory exists
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False  # To display negative signs correctly

# Read data
file_path = "data/run_log.xlsx"
sheet_name = '런로그'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean column names: strip whitespace
df.columns = df.columns.str.strip()

# Find the actual column names containing the keywords to be robust against slight variations
col_metal = None
col_temp = None
col_grade = None

for c in df.columns:
    if '잔류금속' in c:
        col_metal = c
    if '산화개시온도' in c:
        col_temp = c
    if '등급' in c:
        col_grade = c

if col_metal is None or col_temp is None or col_grade is None:
    raise ValueError(f"Could not find required columns. Available: {df.columns.tolist()}")

# Extract relevant columns and convert to numeric for x and y
x_data = pd.to_numeric(df[col_temp], errors='coerce')
y_data = pd.to_numeric(df[col_metal], errors='coerce')
grade_data = df[col_grade].astype(str).str.strip()

# Drop rows where either value is NaN (not a number or missing) or grade is missing
mask_valid = ~x_data.isna() & ~y_data.isna() & ~grade_data.isin(['nan', 'NaN', ''])

# Filter out Grade C as requested
mask_not_c = mask_valid & (grade_data != 'C')

x_clean = x_data[mask_not_c]
y_clean = y_data[mask_not_c]
g_clean = grade_data[mask_not_c]

# Define colors for grades (A green, B orange)
colors = {'A': 'green', 'B': 'orange'}

# Create the plot
plt.figure(figsize=(10, 6))

# Plot each grade separately to create a legend
unique_grades = ['A', 'B']
for g in unique_grades:
    mask_g = g_clean == g
    if any(mask_g):
        plt.scatter(x_clean[mask_g], y_clean[mask_g], 
                    alpha=0.6, edgecolors='w', s=50, 
                    color=colors.get(g, 'gray'), 
                    label=f'Grade {g}')

# Calculate linear regression for all remaining points (A and B combined)
slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
r_squared = r_value**2

# Generate line points for plotting
x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
y_line = slope * x_line + intercept

# Plot the regression line
plt.plot(x_line, y_line, color='black', linestyle='--', linewidth=2, label='1차 회귀선')

# Add labels and title using the found column names for clarity
plt.xlabel(col_temp, fontsize=12)
plt.ylabel(col_metal, fontsize=12)
plt.title('잔류금속 vs 산화개시온도 산점도 (C 등급 제외)', fontsize=14)

# Add grid
plt.grid(True, linestyle='--', alpha=0.7)

# Add legend
plt.legend(title='등급')

# Annotate R² on the plot
text_str = f'$R^2$ = {r_squared:.4f}'
plt.text(0.05, 0.95, text_str, transform=plt.gca().transAxes, 
         fontsize=12, verticalalignment='top', horizontalalignment='left',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

# Save the figure
output_file = os.path.join(OUT_DIR, 'scatter_metal_vs_oxidation_temp_no_C_with_regression.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')

# Close the plot to free memory
plt.close()
