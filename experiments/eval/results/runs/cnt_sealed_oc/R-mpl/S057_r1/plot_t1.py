import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Identify columns by keyword matching to handle potential unit strings in headers or data issues
cols_keywords = ['체류시간', 'H2/C2H4비', '2존온도', '3존온도', '외기습도', 
                 'CNT수율', '잔류금속', '산화개시온도', 'IG/ID']

actual_cols = []
for kw in cols_keywords:
    # Find column that contains the keyword
    matches = [c for c in df.columns if kw in str(c)]
    if matches:
        actual_cols.append(matches[0])
    else:
        raise ValueError(f"Column containing '{kw}' not found in dataframe.")

print(f"Mapped columns: {actual_cols}")

# Extract relevant data and convert to numeric, coercing errors to NaN
correlation_data = df[actual_cols].apply(pd.to_numeric, errors='coerce').dropna()

# Calculate Pearson correlation matrix
corr_matrix = correlation_data.corr(method='pearson')

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_matrix.values, cmap='RdBu_r', vmin=-1, vmax=1)

# Create colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('Pearson Correlation Coefficient', rotation=-90, va="bottom")

# Show ticks
ax.set_xticks(np.arange(len(actual_cols)))
ax.set_yticks(np.arange(len(actual_cols)))

# Shorten labels for better readability: remove units part if present in parentheses
short_labels = []
for c in actual_cols:
    # Split by '(' and take the first part, then strip whitespace
    label = str(c).split('(')[0].strip()
    short_labels.append(label)

ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=10)
ax.set_yticklabels(short_labels, fontsize=10)

# Annotate with values
for i in range(len(actual_cols)):
    for j in range(len(actual_cols)):
        val = corr_matrix.iloc[i, j]
        text_color = "black" if abs(val) < 0.7 else "white"
        text = ax.text(j, i, f"{val:.2f}",
                       ha="center", va="center", color=text_color)

ax.set_title("Pearson Correlation Heatmap of Process Parameters and Quality Metrics")

# Save figure
output_file = os.path.join(OUT_DIR, "pearson_correlation_heatmap.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
