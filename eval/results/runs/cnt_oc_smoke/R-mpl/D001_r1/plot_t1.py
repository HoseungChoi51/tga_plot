import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Load the data from the specified Excel file and sheet
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: remove leading/trailing whitespace to handle potential formatting issues in Excel headers
df.columns = df.columns.str.strip()

# Identify the correct column name for CNT yield
yield_col = None
for col in df.columns:
    if 'CNT수율' in str(col):
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT yield column.")

week_col = '주차'
reactor_col = '반응기'

# Convert relevant columns to numeric types to fix TypeError during mean calculation
# The error suggests the column might be read as object (string) due to hidden characters or mixed types
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')

# Drop rows where conversion failed (NaNs)
df = df.dropna(subset=[week_col, reactor_col, yield_col])

# Filter data to ensure we only have valid weeks (1-26) and reactors (R1-R4)
valid_weeks = range(1, 27)
valid_reactors = ["R1", "R2", "R3", "R4"]

# Calculate mean CNT yield per week per reactor
grouped = df.groupby([week_col, reactor_col])[yield_col].mean().reset_index()

# Pivot the data to have weeks as index and reactors as columns for easier plotting
pivot_df = grouped.pivot(index=week_col, columns=reactor_col, values=yield_col)

# Reindex to ensure all weeks 1-26 are present and sorted correctly
pivot_df = pivot_df.reindex(valid_weeks)

# Create the plot
plt.figure(figsize=(12, 8))

# Plot each reactor line
colors = {'R1': '#1f77b4', 'R2': '#ff7f0e', 'R3': '#2ca02c', 'R4': '#d62728'}
for reactor in valid_reactors:
    if reactor in pivot_df.columns:
        # Interpolate missing values if any week has no runs for a specific reactor, 
        # or just let matplotlib handle NaNs (which breaks the line). 
        # Given it's production data, gaps might exist. We'll plot what's there.
        plt.plot(pivot_df.index, pivot_df[reactor], marker='o', linestyle='-', 
                 label=f"{reactor}", color=colors.get(reactor, None), markersize=5)

# Customize the plot
plt.title("주차별 평균 CNT 수율 추이 (반응기별)", fontsize=16)
plt.xlabel("주차", fontsize=12)
plt.ylabel(f"평균 CNT 수율 ({yield_col})", fontsize=12)
plt.xticks(ticks=list(valid_weeks)) # Ensure ticks are 1 to 26
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(title="반응기", loc="best")

# Adjust layout and save
plt.tight_layout()
output_file = os.path.join(OUT_DIR, "cnt_yield_by_week_and_reactor.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"Plot saved to {output_file}")
