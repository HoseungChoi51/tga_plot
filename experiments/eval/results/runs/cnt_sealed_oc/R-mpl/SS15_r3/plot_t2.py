import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Configure font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify the correct column name for CNT yield by searching for '수율'
col_name = None
for col in df.columns:
    if 'CNT수율' in str(col):
        col_name = col
        break

if col_name is None:
    raise ValueError("Column containing 'CNT수율' not found.")

# Ensure numeric types for plotting columns
df['주차_num'] = pd.to_numeric(df['주차'], errors='coerce')
df['yield_num'] = pd.to_numeric(df[col_name], errors='coerce')

# Filter out rows where either 주차 or 수율 is NaN
df_clean = df.dropna(subset=['주차_num', 'yield_num'])

# Separate data into two periods: Weeks 1-13 and Weeks 14-26
period1_data = df_clean[df_clean['주차_num'] <= 13]['yield_num'].values
period2_data = df_clean[df_clean['주차_num'] >= 14]['yield_num'].values

# Define shared bin edges: 1 g/g-cat wide from 12 to 36
bin_edges = np.arange(12, 37, 1)

# Create overlay histogram
plt.figure(figsize=(10, 6))
plt.hist(period1_data, bins=bin_edges, alpha=0.5, label='주차 1–13', color='steelblue', edgecolor='black')
plt.hist(period2_data, bins=bin_edges, alpha=0.5, label='주차 14–26', color='darkorange', edgecolor='black')

# Add labels and title
plt.xlabel("CNT수율 (g/g-cat)", fontsize=12)
plt.ylabel("빈도 (Count)", fontsize=12)
plt.title("CNT수율 분포 비교: 주차 1–13 vs 14–26", fontsize=14)
plt.legend()
plt.grid(axis='y', alpha=0.75)
plt.grid(axis='x', alpha=0.75)

# Save the plot
output_file = os.path.join(OUT_DIR, "cnt_yield_histogram_overlay.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
