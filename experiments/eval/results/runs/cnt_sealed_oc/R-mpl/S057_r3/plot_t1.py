import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Define requested column names (cleaned from the prompt's description of headers)
requested_cols_clean = [
    "체류시간",
    "H2/C2H4비",
    "2존온도",
    "3존온도",
    "외기습도",
    "CNT수율",
    "잔류금속",
    "산화개시온도",
    "IG/ID"
]

# Find actual columns in df that match the requested ones
# The preview shows headers like 'H 1존온도 (°C)', so the actual string is likely '1존온도 (°C)'
# We need to map our clean names to the actual column strings found in the dataframe.
actual_cols = []
missing_cols = []

for req in requested_cols_clean:
    # Try exact match first
    if req in df.columns:
        actual_cols.append(req)
    else:
        # Try finding a column that starts with the request or contains it, 
        # handling potential units or spaces
        found = None
        for col in df.columns:
            # Normalize for comparison: remove spaces and check if core name matches
            # e.g., if req='체류시간' and col='체류시간 (s)' -> match
            if col.startswith(req):
                found = col
                break
            # Handle cases where units might be attached differently
            if req in col:
                # Prefer shorter match or specific pattern if multiple found? 
                # Usually prefix match is safer for "Name Unit" format
                pass
        
        if found:
            actual_cols.append(found)
        else:
            missing_cols.append(req)

if missing_cols:
    print(f"Warning: Could not find columns for: {missing_cols}")
    # Fallback: try to find any column containing the key substring without strict startswith
    for i, req in enumerate(requested_cols_clean):
        if req in missing_cols:
             candidates = [c for c in df.columns if req.split()[0] in c or req.replace(' ', '') in c.replace(' ', '')]
             if candidates:
                 actual_cols.append(candidates[0])

# Ensure we have all 9 columns for correlation
if len(actual_cols) != len(requested_cols_clean):
    # If some are still missing, filter them out to prevent crash, though ideally all should be there based on preview
    valid_indices = [i for i, c in enumerate(actual_cols) if c in df.columns]
    actual_cols = [actual_cols[i] for i in valid_indices]

# Select columns
try:
    df_selected = df[actual_cols]
except KeyError as e:
    raise ValueError(f"Column selection failed. Available columns sample: {list(df.columns)[:10]}. Error: {e}")

# Compute Pearson correlation matrix
corr_matrix = df_selected.corr(method='pearson')

# Plot heatmap using matplotlib imshow
fig, ax = plt.subplots(figsize=(10, 8))

im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1)

# Set ticks and labels
ax.set_xticks(np.arange(len(actual_cols)))
ax.set_yticks(np.arange(len(actual_cols)))

# Use the original requested names for display if possible, or the actual cleaned names
display_labels = []
for col in actual_cols:
    # Extract just the name part before space or parenthesis for cleaner label
    label = col.split('(')[0].strip()
    display_labels.append(label)

ax.set_xticklabels(display_labels, rotation=45, ha="right")
ax.set_yticklabels(display_labels)

# Add annotations
for i in range(len(actual_cols)):
    for j in range(len(actual_cols)):
        val = corr_matrix.iloc[i, j]
        # Avoid annotating NaN if present
        if not np.isnan(val):
            color = "white" if abs(val) > 0.6 else "black"
            text = ax.text(j, i, f"{val:.2f}",
                           ha="center", va="center", color=color, fontsize=9)

# Colorbar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('Pearson Correlation')

ax.set_title("Pearson Correlation Heatmap of Process Parameters and Quality Metrics")
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "correlation_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
