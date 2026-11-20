import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# The error suggests column names might have extra spaces or slight differences.
# Let's strip whitespace from all column names to be safe and match the preview more closely if needed.
df.columns = df.columns.str.strip()

# Identify columns based on keywords since exact string matching failed previously due to potential hidden chars/spaces
# Preview says: H 2존온도 (°C), Q CNT수율 (g/g-cat)
# We will look for columns containing these substrings
temp_col = None
yield_col = None

for col in df.columns:
    if '2존' in col and '온도' in col:
        temp_col = col
    elif 'CNT' in col and '수율' in col:
        yield_col = col

if temp_col is None or yield_col is None:
    # Fallback: print columns to debug if strictly necessary, but we must return a script that runs.
    # Assuming standard naming if specific ones aren't found, but let's try to map by position or common patterns.
    # If the previous error was KeyError on those specific strings, it means they don't exist exactly.
    # Let's inspect available columns dynamically in the script logic if static fails, 
    # but usually, stripping whitespace fixes it.
    
    # Let's try a more robust search
    for col in df.columns:
        if temp_col is None and ('2존' in str(col)) and ('온도' in str(col)):
            temp_col = col
        if yield_col is None and ('CNT' in str(col)) and ('수율' in str(col)):
            yield_col = col
            
if temp_col is None:
    # Last resort: assume column index if names are garbled, but risky. 
    # Based on preview: H is index 7 (0-indexed), Q is index 16 (0-indexed)
    temp_col = df.columns[7]
    yield_col = df.columns[16]

# Clean data
relevant_cols = [temp_col, yield_col]
df_clean = df.dropna(subset=relevant_cols).copy()

# Ensure numeric types
df_clean[temp_col] = pd.to_numeric(df_clean[temp_col], errors='coerce')
df_clean[yield_col] = pd.to_numeric(df_clean[yield_col], errors='coerce')
df_clean = df_clean.dropna(subset=relevant_cols)

if df_clean.empty:
    print("No valid data found after cleaning.")
else:
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = df_clean[temp_col]
    y = df_clean[yield_col]
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors='w', s=50, color='steelblue', label='Data Points')
    
    # Add a trend line to visualize relationship
    # Calculate correlation for context
    corr = np.corrcoef(x, y)[0, 1]
    
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Trend Line (Slope={z[0]:.3f}, R={corr:.3f})')
    
    # Labels and Title
    ax.set_xlabel(temp_col, fontsize=12)
    ax.set_ylabel(yield_col, fontsize=12)
    ax.set_title('2존 온도와 CNT 수율의 상관관계', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Save figure
    output_filename = os.path.join(OUT_DIR, 'zone2_temp_vs_yield.png')
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f"Plot saved to {output_filename}")
