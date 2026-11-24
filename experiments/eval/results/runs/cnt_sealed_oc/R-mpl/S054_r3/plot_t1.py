import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configuration
OUT_DIR = "out/t1"
DATA_FILE = "data/run_log.xlsx"
SHEET_NAME = "런로그"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Font configuration for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# Clean column names to handle potential whitespace issues from Excel
df.columns = df.columns.str.strip()

# Robust column selection: find columns by partial matching or exact known variations
def get_col(df, target_substr):
    """Find a column in df that contains the target substring."""
    cols = [c for c in df.columns if target_substr in c]
    if not cols:
        raise KeyError(f"Column containing '{target_substr}' not found in {df.columns.tolist()}")
    return cols[0]

try:
    col_reactor = get_col(df, "반응기")
    col_humidity = get_col(df, "외기습도") # Matches '외기습도 (%)' or similar
    col_metal = get_col(df, "잔류금속")   # Matches '잔류금속 (wt%)' or similar
except Exception as e:
    print(f"Error finding columns: {e}")
    # Fallback to exact indices if headers are completely weird, though preview suggests standard structure
    # Column E is 반응기, O is 외기습도 (%), S is 잔류금속 (wt%) based on 1-based indexing in description (A=1, B=2...)
    # In Python 0-based: E->4, O->14, S->18
    col_reactor = df.columns[4]
    col_humidity = df.columns[14]
    col_metal = df.columns[18]

# Force numeric conversion for humidity and metal columns to fix TypeError during comparison
# This handles cases where cells might be strings due to formatting or mixed types in Excel
df[col_humidity] = pd.to_numeric(df[col_humidity], errors='coerce')
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')

# Create humidity bands
# <60 -> Low
# 60–75 -> Mid
# >=75 -> High
def get_humidity_band(h):
    if pd.isna(h):
        return np.nan
    if h < 60:
        return "<60%"
    elif h <= 75:
        return "60-75%"
    else:
        return "≥75%"

df["습도구간"] = df[col_humidity].apply(get_humidity_band)

# Define order for plotting consistency
humidity_order = ["<60%", "60-75%", "≥75%"]
reactors = sorted([r for r in df[col_reactor].unique() if isinstance(r, str)])

# Pivot table to get mean metal residue by reactor and humidity band
pivot_df = df.pivot_table(index=col_reactor, 
                          columns="습도구간", 
                          values=col_metal, 
                          aggfunc="mean")

# Reindex to ensure all reactors and bands are present and ordered correctly
pivot_df = pivot_df.reindex(columns=humidity_order, fill_value=np.nan)
pivot_df = pivot_df.loc[reactors]

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(pivot_df.index))  # label locations
width = 0.25  # width of bars
multiplier = 0

colors = ['#4C72B0', '#DD8452', '#55A868'] # Distinct colors for humidity bands

for i, hum_band in enumerate(humidity_order):
    offset = width * multiplier
    rects = ax.bar(x + offset, pivot_df[hum_band], width, label=hum_band, color=colors[i])
    ax.bar_label(rects, padding=3, fmt='%.2f')
    multiplier += 1

# Add some spacing between the groups if desired (optional, standard grouped bar often just places them adjacent)
# To make it clearer that these are grouped by Reactor, we set xticks to center of each group
ax.set_xticks(x + width, labels=pivot_df.index)
ax.set_xlabel("반응기", fontsize=12)
ax.set_ylabel("평균 잔류금속 (wt%)", fontsize=12)
ax.set_title("반응기별 외기습도 구간 평균 잔류금속 비교", fontsize=14, fontweight='bold')

# Legend
ax.legend(title="외기습도 구간", loc="upper left", ncols=1)

# Grid and styling
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "metal_residue_by_reactor_humidity.png")
plt.savefig(output_path, dpi=300)
plt.close()
