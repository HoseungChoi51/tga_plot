import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Setup
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"

# Read all sheets
xl_file = pd.ExcelFile(file_path)
sheet_names = xl_file.sheet_names

fig, ax = plt.subplots(figsize=(10, 6))

for sheet in sheet_names:
    df = pd.read_excel(xl_file, sheet_name=sheet)
    
    # Identify columns based on preview description: 
    # B 온도 (°C), D 미분중량 (%/°C)
    # Headers might vary slightly in whitespace or exact text, but typically the second and fourth columns are Temperature and Derivative Weight.
    # Let's find the column names containing '온도' and '미분중량' or just use indices if headers are tricky.
    # Safer approach: search for keywords in column names
    
    temp_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col)
        if '온도' in col_str:
            temp_col = col
        elif '미분' in col_str or 'derivative' in col_str.lower():
            dtg_col = col
            
    # Fallback to index if keywords not found exactly (based on preview: A time, B temp, C weight, D deriv)
    if temp_col is None and len(df.columns) > 1:
        temp_col = df.columns[1]
    if dtg_col is None and len(df.columns) > 3:
        dtg_col = df.columns[3]
        
    if temp_col is None or dtg_col is None:
        continue
        
    # Filter data for 500-700 °C
    mask = (df[temp_col] >= 500) & (df[temp_col] <= 700)
    filtered_df = df[mask].dropna(subset=[temp_col, dtg_col])
    
    if filtered_df.empty:
        continue
        
    x_vals = filtered_df[temp_col]
    y_vals = filtered_df[dtg_col]
    
    # Plot DTG curve
    label = f"{sheet}"
    ax.plot(x_vals, y_vals, label=label, linewidth=1.5)
    
    # Find peak location in this range
    max_idx = y_vals.idxmax()
    peak_temp = filtered_df.loc[max_idx, temp_col]
    peak_val = filtered_df.loc[max_idx, dtg_col]
    
    # Annotate peak value (optional, user asked to show values, but 10 labels might clutter. 
    # User said "Write values the user asks to show on the plot as text." 
    # The request was just to compare peak locations. I will add a table or annotate the peaks clearly.)
    # To avoid clutter, I'll mark the peaks with a dot and put a legend. 
    # Or better, create a small summary table at the end? 
    # Let's stick to marking the peaks on the line itself if possible, or just rely on the visual comparison.
    # Given "피크 위치 비교", highlighting the peak point is good practice.
    ax.scatter([peak_temp], [peak_val], s=20, zorder=5)

ax.set_title('DTG 곡선 비교 (500–700 °C 구간)')
ax.set_xlabel('온도 (°C)')
ax.set_ylabel('미분중량 (%/°C)')
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(loc='best', fontsize=8, ncol=2)

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "tga_dtg_comparison_500_700.png")
plt.savefig(output_filename, dpi=300)
plt.close()
