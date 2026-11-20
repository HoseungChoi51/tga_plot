import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to remove potential whitespace issues from Excel headers
df.columns = df.columns.str.strip()

# Identify the correct columns by matching keywords since exact header strings might vary slightly
# We look for columns containing '산화개시온도' and '잔류금속'
x_col_candidates = [col for col in df.columns if '산화개시온도' in str(col)]
y_col_candidates = [col for col in df.columns if '잔류금속' in str(col)]

if not x_col_candidates or not y_col_candidates:
    raise ValueError("Could not find required columns: 산화개시온도 or 잔류금속")

x_col = x_col_candidates[0]
y_col = y_col_candidates[0]

# Ensure numeric types
df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

# Drop rows with missing values in these columns for plotting
plot_df = df.dropna(subset=[x_col, y_col])

# Create the plot
fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(plot_df[x_col], plot_df[y_col], alpha=0.6, edgecolors='k', s=50)

# Add labels and title using the actual column names found (or standard ones if they are clean)
# For display purposes, we use the cleaned variable names which reflect the content
ax.set_xlabel(x_col, fontsize=12)
ax.set_ylabel(y_col, fontsize=12)
ax.set_title("잔류금속 vs 산화개시온도 산점도 (전체 런)", fontsize=14)

# Add grid
ax.grid(True, linestyle='--', alpha=0.7)

# Save figure
output_filename = os.path.join(OUT_DIR, "scatter_residual_metal_vs_onset_temp.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
