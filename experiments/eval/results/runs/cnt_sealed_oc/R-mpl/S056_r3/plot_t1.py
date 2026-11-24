import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
df = pd.read_excel("data/downtime.xlsx", sheet_name="정지이력")

# Filter valid numeric downtime values
downtime_data = df["정지시간(분)"].dropna()

# Define log-spaced bin edges
bins = [5, 10, 20, 50, 100, 200, 500, 1000]

# Create histogram
fig, ax = plt.subplots(figsize=(8, 6))
counts, bins_edges, patches = ax.hist(downtime_data, bins=bins, edgecolor='black', alpha=0.7)

# Set x-axis to logarithmic scale
ax.set_xscale('log')
ax.set_xticks(bins)
ax.set_xticklabels([str(b) for b in bins])

# Labels and title
ax.set_xlabel("정지시간 (분)")
ax.set_ylabel("빈도 (Count)")
ax.set_title("CNT 생산 정지 시간 분포 (Histogram of Downtime)")

# Grid
ax.grid(True, which="both", ls="--", linewidth=0.5)

# Save figure
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "downtime_histogram.png"), dpi=300)
plt.close()
