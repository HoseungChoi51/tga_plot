import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t2"
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
mask = ~x_data.isna() & ~y_data.isna() & ~grade_data.isin(['nan', 'NaN', ''])
x_clean = x_data[mask]
y_clean = y_data[mask]
g_clean = grade_data[mask]

# Define colors for grades
colors = {'A': 'green', 'B': 'orange', 'C': 'red'}

# Create the plot
plt.figure(figsize=(10, 6))

# Plot each grade separately to create a legend
unique_grades = ['A', 'B', 'C']
for g in unique_grades:
    mask_g = g_clean == g
    if any(mask_g):
        plt.scatter(x_clean[mask_g], y_clean[mask_g], 
                    alpha=0.6, edgecolors='w', s=50, 
                    color=colors.get(g, 'gray'), 
                    label=f'Grade {g}')

# Add labels and title using the found column names for clarity
plt.xlabel(col_temp, fontsize=12)
plt.ylabel(col_metal, fontsize=12)
plt.title('잔류금속 vs 산화개시온도 산점도 (등급별 구분)', fontsize=14)

# Add grid
plt.grid(True, linestyle='--', alpha=0.7)

# Add legend
plt.legend(title='등급')

# Save the figure
output_file = os.path.join(OUT_DIR, 'scatter_metal_vs_oxidation_temp_by_grade.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')

# Close the plot to free memory
plt.close()
