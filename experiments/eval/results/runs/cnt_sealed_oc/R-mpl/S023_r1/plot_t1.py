import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# Identify columns based on preview description
# Preview: S 잔류금속 (wt%), U IG/ID, V 등급 (A/B/C)
# We need to map these. The header text in Excel might be exactly '잔류금속 (wt%)' or similar.
# Let's find columns containing the keywords to be robust.

col_metal = None
col_raman = None
col_grade = None

for col in df.columns:
    str_col = str(col)
    if '잔류금속' in str_col and 'IG' not in str_col: # Exclude Raman col if it somehow contains metal keyword? Unlikely but safe.
        col_metal = col
    elif 'IG/ID' in str_col:
        col_raman = col
    elif '등급' in str_col:
        col_grade = col

if not all([col_metal, col_raman, col_grade]):
    raise ValueError(f"Could not find required columns. Found: {col_metal}, {col_raman}, {col_grade}")

# Filter out Grade C
# Ensure grade column is string type for comparison
df[col_grade] = df[col_grade].astype(str).str.strip()
df_filtered = df[df[col_grade] != 'C'].copy()

# Select relevant columns and drop NaNs
# Convert to numeric to ensure calculation works, coercing errors to NaN just in case of stray text
x_series = pd.to_numeric(df_filtered[col_metal], errors='coerce')
y_series = pd.to_numeric(df_filtered[col_raman], errors='coerce')

# Combine into a temporary dataframe to drop rows where either is NaN
mask = ~np.isnan(x_series.values) & ~np.isnan(y_series.values)
x_data = x_series[mask].values
y_data = y_series[mask].values

if len(x_data) < 2:
    raise ValueError("Not enough valid data points after filtering.")

# Perform linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
r_squared = r_value**2

# Generate regression line points
min_x = np.min(x_data)
max_x = np.max(x_data)
x_line = np.array([min_x, max_x])
y_line = slope * x_line + intercept

# Plotting
fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(x_data, y_data, color='steelblue', alpha=0.6, edgecolors='w', s=50, label='데이터 (Grade A, B)')
ax.plot(x_line, y_line, color='red', linestyle='--', linewidth=2, label='회귀선')

# Add regression equation and R^2
eq_text = f'y = {slope:.4f}x + {intercept:.4f}'
r2_text = f'$R^2$ = {r_squared:.4f}'
textstr = '\n'.join((eq_text, r2_text))

props = dict(boxstyle='round', facecolor='white', alpha=0.8)
ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='right', bbox=props)

ax.set_xlabel('잔류금속 (wt%)', fontsize=14)
ax.set_ylabel('IG/ID', fontsize=14)
ax.set_title('잔류금속 vs IG/ID 산점도 및 회귀 분석 (Grade C 제외)', fontsize=16)
ax.legend(loc='lower right', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
output_file = os.path.join(OUT_DIR, "scatter_residual_metal_vs_igid.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
