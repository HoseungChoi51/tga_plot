import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to handle potential whitespace issues causing KeyError
df_runs.columns = df_runs.columns.str.strip()

# Identify the yield column robustly
yield_col = None
for col in df_runs.columns:
    if 'CNT수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    # Fallback if exact match fails but we know it's usually Q or similar
    # Based on preview: Q CNT수율 (g/g-cat)
    # If still not found, print columns for debugging in real scenario, but here we assume standard structure
    raise ValueError("Could not find CNT Yield column. Available columns: " + str(df_runs.columns.tolist()))

# Convert date column to datetime safely
# The previous error suggested 'yyyy-mm-dd' literal string might be present or mixed types.
# We try to coerce errors to NaT and drop those rows.
date_col = None
for col in df_runs.columns:
    if '일자' in str(col):
        date_col = col
        break
        
if date_col is None:
     # Fallback based on preview B 일자
     date_col = '일자'

df_runs[date_col] = pd.to_datetime(df_runs[date_col], errors='coerce')

# Drop rows where date conversion failed (if any)
df_runs = df_runs.dropna(subset=[date_col])

# Sort by date for clear trend visualization
df_runs = df_runs.sort_values(date_col)

# Calculate a 7-day moving average of yield
# Using the identified column name
df_runs['수율_이동평균_7일'] = df_runs[yield_col].rolling(window=7, min_periods=1).mean()

# Create the plot
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot individual run yields as scatter points (light color)
ax1.scatter(df_runs[date_col], df_runs[yield_col], 
            color='steelblue', alpha=0.3, s=15, label='개별 런 수율')

# Plot the 7-day moving average as a line (bold color)
ax1.plot(df_runs[date_col], df_runs['수율_이동평균_7일'], 
         color='darkred', linewidth=2.5, label='7일 이동평균 수율')

# Formatting
ax1.set_xlabel('일자', fontsize=12)
ax1.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax1.tick_params(axis='both', which='major', labelsize=10)
ax1.grid(True, linestyle='--', alpha=0.5)

# Add title and legend
ax1.set_title('기간에 따른 CNT 생산 수율 추이', fontsize=14, pad=15)
ax1.legend(loc='upper left', fontsize=10)

# Rotate x-axis labels for better readability
fig.autofmt_xdate()

# Save figure
output_file = os.path.join(OUT_DIR, "yield_trend_over_time.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
