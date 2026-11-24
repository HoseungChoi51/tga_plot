import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Data Loading
file_path = 'data/run_log.xlsx'
sheet_name = '런로그'

try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    raise ValueError(f"Failed to read Excel file: {e}")

# Ensure column name matches exactly (Korean header)
worker_col = '작업자'
if worker_col not in df.columns:
    # Fallback if header has spaces or slight variations, though preview says 'G 작업자'
    possible_cols = [c for c in df.columns if '작업자' in str(c)]
    if possible_cols:
        worker_col = possible_cols[0]
    else:
        raise KeyError("Column '작업자' not found.")

# 2. Data Processing
# Count runs per worker
run_counts = df[worker_col].value_counts()

# Sort by count descending for better visualization
run_counts = run_counts.sort_values(ascending=False)

# Calculate percentages
total_runs = run_counts.sum()
percentages = (run_counts / total_runs) * 100

# Prepare labels and sizes for pie chart
labels = run_counts.index.tolist()
sizes = run_counts.values

# Create output directory if it doesn't exist
out_dir = "out"
os.makedirs(out_dir, exist_ok=True)
output_file = os.path.join(out_dir, "worker_run_ratio.png")

# 3. Plotting
plt.rcParams["font.family"] = "Noto Sans CJK KR"

fig, ax = plt.subplots(figsize=(10, 8))

# Define colors for the pie slices
colors = plt.cm.tab20(range(len(labels)))

# Draw pie chart
wedges, texts, autotexts = ax.pie(
    sizes, 
    labels=labels, 
    autopct='%1.1f%%', 
    startangle=90,
    pctdistance=0.85,
    colors=colors,
    wedgeprops=dict(edgecolor='white', linewidth=1.5)
)

# Style text elements
for text in texts + autotexts:
    text.set_fontsize(12)
    
ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

# Title and layout
plt.title('작업자별 런 수 비율', fontsize=16, pad=20)
plt.tight_layout()

# Save figure
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plot saved to {output_file}")
