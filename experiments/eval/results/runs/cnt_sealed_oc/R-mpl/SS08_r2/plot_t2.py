import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t2"
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

# Drop rows with missing values in these columns for plotting
plot_df = df.dropna(subset=[x_col, y_col])

# Define colors for grades
color_map = {
    'A': 'green',
    'B': 'orange',
    'C': 'red'
}

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

# Plot each grade separately to get distinct legends and colors
for grade, color in color_map.items():
    subset = plot_df[plot_df[grade_col] == grade]
    if not subset.empty:
        ax.scatter(subset[x_col], subset[y_col], 
                   alpha=0.6, edgecolors='k', s=50, 
                   label=f'Grade {grade}', color=color)

# Add labels and title
ax.set_xlabel(x_col, fontsize=12)
ax.set_ylabel(y_col, fontsize=12)
ax.set_title("잔류금속 vs 산화개시온도 산점도 (전체 런)", fontsize=14)

# Add legend
ax.legend(title="등급", loc="best")

# Add grid
ax.grid(True, linestyle='--', alpha=0.7)

# Save figure
output_filename = os.path.join(OUT_DIR, "scatter_residual_metal_vs_onset_temp.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
