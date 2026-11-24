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

# Read the Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify the correct column name for operating time
col_candidates = [c for c in df.columns if '가동시간' in str(c)]
if not col_candidates:
    raise ValueError("Column containing '가동시간' not found.")
operating_time_col = col_candidates[0]

# Extract operating time data and ensure it is numeric
operating_times = pd.to_numeric(df[operating_time_col], errors='coerce').dropna()

# Define histogram bins: 2 to 17 with interval of 1
# We want bars centered or edges at integers. 
# To show distribution from 2h to 17h clearly with 1h gaps, we define edges:
# 2, 3, ..., 17, 18? No, the request says range 2~17. 
# If a run is 16.5h, it falls into [16, 17). 
# Let's use edges that create bins [2,3), [3,4), ..., [16,17), [17,18) maybe? 
# The user asked for "1시간 간격으로 2~17 h 범위". This usually means bins covering this span.
# Data max is 16.5. So bins up to 17 are sufficient.
# Edges: 2, 3, 4, ..., 17. This creates 15 bins. 
# The last bin is [16, 17). Since max is 16.5, this covers all data > 2.
bins = np.arange(2, 18, 1) 

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot histogram
ax.hist(operating_times, bins=bins, edgecolor='black', alpha=0.7, color='#4C72B0')

# Labels and Title
ax.set_xlabel('가동시간 (h)', fontsize=12)
ax.set_ylabel('빈도 수 (Count)', fontsize=12)
ax.set_title('가동시간 분포 히스토그램', fontsize=14)

# Add grid for better readability
ax.grid(axis='y', linestyle='--', alpha=0.5)

# Adjust layout
plt.tight_layout()

# Save the figure
output_file = os.path.join(OUT_DIR, "operating_time_histogram.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')

# Close the plot to prevent display
plt.close(fig)

print(f"Plot saved to {output_file}")
