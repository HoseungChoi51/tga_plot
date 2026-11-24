import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# Filter for TEM-03 sample only
tem_03_df = df[df['시료'] == 'TEM-03']

# Extract diameter values
diameters = tem_03_df['직경(nm)'].dropna()

# Determine appropriate bins using Sturges' formula or similar heuristic
n_data = len(diameters)
if n_data > 0:
    # Using Sturges' rule: k = ceil(log2(n)) + 1
    num_bins = int(np.ceil(np.log2(n_data)) + 1)
    
    # Plot histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    
    counts, bins, patches = ax.hist(diameters, bins=num_bins, edgecolor='black', color='skyblue', alpha=0.7)
    
    ax.set_title('TEM-03 시료 직경 분포', fontsize=14)
    ax.set_xlabel('직경 (nm)', fontsize=12)
    ax.set_ylabel('빈도', fontsize=12)
    
    # Add mean and median lines for reference
    mean_val = diameters.mean()
    median_val = diameters.median()
    ax.axvline(mean_val, color='red', linestyle='dashed', linewidth=1.5, label=f'평균: {mean_val:.2f} nm')
    ax.axvline(median_val, color='green', linestyle='dashed', linewidth=1.5, label=f'중위값: {median_val:.2f} nm')
    ax.legend(loc='best')
    
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Save figure
    save_path = os.path.join(OUT_DIR, "tem03_diameter_distribution.png")
    plt.savefig(save_path, dpi=300)
    plt.close()
else:
    print("No data found for TEM-03")
