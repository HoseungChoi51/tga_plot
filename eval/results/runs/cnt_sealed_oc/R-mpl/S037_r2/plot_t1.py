import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/L3_MES_export_202607.csv"

# The previous error indicated that reading it as Excel failed or resulted in wrong columns, 
# and reading as CSV with default delimiter failed due to inconsistent fields.
# Given the file extension is .csv but the preview mentions a 'Sheet' name, this is often an 
# exported Excel file where the data might be tab-separated or have specific quirks.
# However, the most robust way for these industrial exports which fail standard parsing is 
# to try multiple common delimiters with the python engine which handles ragged rows better.

df = None
possible_delims = [',', ';', '\t', '|']

for delim in possible_delims:
    try:
        # Read with header=0, assuming first row is header. 
        # Use encoding='utf-8-sig' to handle potential BOMs from Windows/Excel exports.
        temp_df = pd.read_csv(file_path, sep=delim, engine='python', encoding='utf-8-sig')
        
        # Check if we found likely column names. If not, continue to next delimiter.
        # We look for keywords '가동시간' and '수율' in column names.
        cols_lower = [str(c).lower() for c in temp_df.columns]
        has_time = any('가동시간' in str(c) or 'operating time' in str(c).lower() for c in temp_df.columns)
        has_yield = any('수율' in str(c) or 'yield' in str(c).lower() for c in temp_df.columns)
        
        if has_time and has_yield:
            df = temp_df
            break
    except Exception:
        continue

if df is None:
    # Last resort: Try reading as Excel again but force openpyxl, sometimes csv files are actually xlsx renamed
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        raise RuntimeError(f"Could not parse {file_path} as CSV or Excel")

# Clean column names
df.columns = df.columns.str.strip()

# Identify columns using fuzzy matching on keywords to avoid KeyError due to exact string mismatch
col_time = None
col_yield = None

for col in df.columns:
    col_str = str(col)
    if '가동시간' in col_str:
        col_time = col
    if 'CNT수율' in col_str or ('수율' in col_str and 'CNT' in col_str.upper()):
        col_yield = col

# Fallback if specific naming doesn't match exactly
if col_time is None:
    matches = [c for c in df.columns if '시간' in str(c)]
    if matches: col_time = matches[0]

if col_yield is None:
    matches = [c for c in df.columns if '수율' in str(c)]
    if matches: col_yield = matches[0]

if col_time is None or col_yield is None:
    print("Columns found:", df.columns.tolist())
    raise ValueError(f"Could not find required columns. Time: {col_time}, Yield: {col_yield}")

# Ensure numeric types
df[col_time] = pd.to_numeric(df[col_time], errors='coerce')
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')

# Drop rows with NaN in these key columns for plotting
plot_df = df.dropna(subset=[col_time, col_yield])

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

# Scatter plot
ax.scatter(plot_df[col_time], plot_df[col_yield], alpha=0.7, edgecolors='w', s=80, color='#1f77b4')

# Labels and Title
ax.set_xlabel('가동시간 (h)', fontsize=12)
ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('L3 파일럿 데이터: 가동시간 vs CNT 수율', fontsize=14)

# Grid
ax.grid(True, linestyle='--', alpha=0.6)

# Save figure
output_filename = os.path.join(OUT_DIR, "scatter_operating_time_vs_yield.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
