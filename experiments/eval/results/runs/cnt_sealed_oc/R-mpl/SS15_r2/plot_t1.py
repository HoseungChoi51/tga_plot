import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and ensure it exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Find the column name for CNT yield. The header might have slight variations or whitespace issues.
yield_col = None
for col in df.columns:
    if isinstance(col, str) and 'CNT' in col and '수율' in col:
        yield_col = col
        break

if yield_col is None:
    # Fallback to just '수율'
    for col in df.columns:
        if isinstance(col, str) and '수율' in col:
            yield_col = col
            break

# Extract CNT yield data
if yield_col is not None:
    # Ensure the data is numeric. Sometimes Excel cells contain strings or empty values that become NaN or objects.
    # astype(float) will convert string numbers to float and fail on non-numeric strings (which become NaN).
    try:
        yield_data = pd.to_numeric(df[yield_col], errors='coerce').dropna()
    except Exception:
        yield_data = df[yield_col].dropna().astype(float)
else:
    # If column still not found, try by index (Q is index 16, assuming A=0)
    # But let's print columns to debug if needed, though we must return code.
    # Using a safe fallback based on typical structure if names are totally weird.
    if len(df.columns) > 16:
         yield_data = pd.to_numeric(df.iloc[:, 16], errors='coerce').dropna()
    else:
         raise ValueError("Could not find CNT Yield column")

# Create histogram with 30 bins
plt.figure(figsize=(10, 6))
plt.hist(yield_data, bins=30, edgecolor='black', color='steelblue')

# Add labels and title
plt.title('CNT 수율 분포 (Histogram of CNT Yield)', fontsize=14)
plt.xlabel('CNT 수율 (g/g-cat)', fontsize=12)
plt.ylabel('빈도 (Frequency)', fontsize=12)

# Save the plot
output_file = os.path.join(OUT_DIR, "cnt_yield_histogram.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
