import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: remove whitespace and normalize to match expected keys if needed
# The error suggests the exact string 'C2H4유량 (sccm)' wasn't found. 
# Let's inspect actual columns to find the closest match or clean them.
actual_columns = df.columns.tolist()

def find_column(df, target):
    """Find a column name that matches the target closely (ignoring extra spaces)."""
    # Normalize function: strip spaces, lower case for comparison
    normalized_target = target.replace(" ", "").lower()
    
    for col in actual_columns:
        normalized_col = str(col).replace(" ", "").lower()
        if normalized_col == normalized_target:
            return col
    # Fallback: check if target is substring or vice versa after normalization
    for col in actual_columns:
        normalized_col = str(col).replace(" ", "").lower()
        if normalized_target in normalized_col or normalized_col in normalized_target:
             return col
    return None

# Try to find the correct columns based on preview description but handling potential whitespace issues
x_col_name = find_column(df, "C2H4유량(sccm)")
y_col_name = find_column(df, "생산속도(g/h)")
group_col_name = find_column(df, "반응기")

# If specific finds fail, try direct assignment with cleaned names from original list
if x_col_name is None:
    # Search manually in case of special characters or unexpected spacing
    for c in actual_columns:
        if "C2H4" in c and "sccm" in c.lower():
            x_col_name = c
            break

if y_col_name is None:
    for c in actual_columns:
        if "생산속도" in c and "g/h" in c.lower():
            y_col_name = c
            break
            
if group_col_name is None:
    for c in actual_columns:
        if "반응기" in c:
            group_col_name = c
            break

# Final fallback validation
if x_col_name is None or y_col_name is None or group_col_name is None:
    raise ValueError(f"Could not identify required columns. Found: {actual_columns}")

print(f"Using X column: '{x_col_name}', Y column: '{y_col_name}', Group column: '{group_col_name}'")

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Plot scatter for each reactor
reactors = sorted(df[group_col_name].unique())
colors = plt.cm.tab10(np.linspace(0, 1, len(reactors)))

for i, reactor in enumerate(reactors):
    subset = df[df[group_col_name] == reactor]
    ax.scatter(subset[x_col_name], subset[y_col_name], 
               label=f'{reactor}', 
               color=colors[i], 
               alpha=0.7, 
               s=50,
               edgecolors='w',
               linewidth=0.5)

# Add labels and title
ax.set_xlabel('C2H4 유량 (sccm)', fontsize=12)
ax.set_ylabel('생산속도 (g/h)', fontsize=12)
ax.set_title('생산속도 vs C2H4 유량 (반응기별 분포)', fontsize=14, fontweight='bold')

# Add legend
ax.legend(title='반응기', loc='best')

# Add grid
ax.grid(True, linestyle='--', alpha=0.6)

# Tight layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "production_rate_vs_c2h4_flow_by_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close(fig)
