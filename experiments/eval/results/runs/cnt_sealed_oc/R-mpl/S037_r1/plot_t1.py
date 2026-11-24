import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# File path
file_path = "data/L3_MES_export_202607.csv"

# Read data
# The previous errors indicate delimiter issues (semicolons/comma mix) and encoding issues.
# Strategy: Try reading with utf-8 first using the python engine which handles mixed delimiters better via sep=None,
# then fallback to other encodings if that fails completely. 
# Given the error "Expected 2 fields... saw 5", it's highly likely a semicolon-delimited file with decimal commas or similar messiness.
# Let's try 'utf-8' with 'python' engine and sep=None first. If headers are garbled, we might need to handle encoding differently.
# However, the second error was cp949 decode error on byte 0xbf. This suggests the file is NOT cp949 encoded in that spot, or partially UTF-8.
# Often Korean CSV exports from MES systems are UTF-8 with BOM or just UTF-8.

df = None
encodings_to_try = ['utf-8-sig', 'utf-8', 'euc-krs', 'cp949']
seps_to_try = [None, ';', ',']

for enc in encodings_to_try:
    for sep in seps_to_try:
        try:
            # Using engine='python' allows more flexible parsing of inconsistent rows
            temp_df = pd.read_csv(file_path, encoding=enc, sep=sep, engine='python')
            
            # Heuristic check: Does it have reasonable column names?
            # We expect columns like '가동시간(h)' and 'CNT수율(g/g-cat)'
            cols_str = ''.join(temp_df.columns.astype(str))
            if '가동시간' in cols_str or 'CNT수율' in cols_str or '수율' in cols_str:
                df = temp_df
                print(f"Successfully loaded with encoding={enc}, sep={sep}")
                break
        except Exception:
            continue
    
    if df is not None:
        break

if df is None:
    # Last resort: read raw lines and try to parse manually or force common defaults
    # If auto-detection failed, let's try forcing utf-8 with semicolon separator as per typical Korean export formats mentioned in prompt ("one CSV export uses semicolons")
    try:
        df = pd.read_csv(file_path, encoding='utf-8', sep=';', engine='python')
    except Exception:
        raise ValueError("Could not load the CSV file with known patterns.")

# Identify columns
# Look for operation time and yield columns flexibly
x_col = None
y_col = None

for col in df.columns:
    col_name = str(col).strip()
    if '가동시간' in col_name:
        x_col = col
    elif '수율' in col_name or 'Yield' in col_name:
        y_col = col

if x_col is None or y_col is None:
    # Fallback to positional or partial match if exact keywords weren't found in headers
    cols_list = df.columns.tolist()
    for i, col in enumerate(cols_list):
        if x_col is None and ('가동' in str(col) or 'Time' in str(col)):
            x_col = col
        if y_col is None and ('수율' in str(col) or 'Yield' in str(col)):
            y_col = col

# Final check
if x_col is None or y_col is None:
    # Print available columns to help debug if logic fails, but script must run.
    # Assume standard positions if names are totally different due to bad parsing: D is time, E is yield based on preview
    # Preview said: D 가동시간(h), E CNT수율(g/g-cat)
    # Index 3 and 4 usually correspond to these if header row is parsed correctly.
    if len(df.columns) >= 5:
        x_col = df.columns[3]
        y_col = df.columns[4]
    else:
        raise ValueError("Cannot identify X and Y columns.")

# Convert to numeric
df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

# Drop NaNs for plotting
df_plot = df.dropna(subset=[x_col, y_col])

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

scatter = ax.scatter(
    df_plot[x_col], 
    df_plot[y_col], 
    alpha=0.7, 
    edgecolors='w', 
    s=100,
    c='steelblue'
)

ax.set_xlabel('가동시간 (h)', fontsize=12)
ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('L3 파일럿 데이터: 가동시간 vs CNT 수율', fontsize=14)

ax.grid(True, linestyle='--', alpha=0.5)

output_filename = os.path.join(OUT_DIR, "l3_operation_time_vs_yield.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
