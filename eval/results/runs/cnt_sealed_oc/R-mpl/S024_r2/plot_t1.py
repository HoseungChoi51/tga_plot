import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# 1. Load Run Log Data
run_log_path = "data/run_log.xlsx"
df_run = pd.read_excel(run_log_path, sheet_name="런로그")

# Identify the correct column for Residual Metal
# The error suggests '잔류금속 (wt%)' might not be exact or has different spacing/characters.
# We look for a column containing '잔류금속'.
metal_col = None
for col in df_run.columns:
    if '잔류금속' in str(col):
        metal_col = col
        break

if metal_col is None:
    raise ValueError("Could not find '잔류금속' column in run log.")

# Prepare a dictionary for quick lookup of residual metal by Run ID
# Ensure Run IDs are strings and stripped for matching with sheet names
df_run['런ID_clean'] = df_run['런ID'].astype(str).str.strip()
residual_map = dict(zip(df_run['런ID_clean'], df_run[metal_col]))

# 2. Load TGA Data
tga_path = "data/tga_batches.xlsx"
tga_sheets = pd.ExcelFile(tga_path).sheet_names

results = []

for sheet in tga_sheets:
    # Read sheet
    df_tga = pd.read_excel(tga_path, sheet_name=sheet)
    
    # Identify columns based on preview:
    # B 온도 (°C), C 중량 (%)
    temp_col = None
    weight_col = None
    
    for col in df_tga.columns:
        if '온도' in str(col):
            temp_col = col
        elif '중량' in str(col) and '미분' not in str(col):
            weight_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    # Extract data at ~800°C
    # Find index closest to 800
    mask_800 = (df_tga[temp_col] >= 795) & (df_tga[temp_col] <= 805)
    subset = df_tga[mask_800]
    
    if subset.empty:
        # If no exact match, take nearest neighbor
        idx = (df_tga[temp_col] - 800).abs().idxmin()
        weight_at_800 = df_tga.loc[idx, weight_col]
    else:
        # Average if multiple points fall in range
        weight_at_800 = subset[weight_col].mean()
        
    # Calculate Fe equivalent
    # Formula: Weight % * 0.699
    fe_equiv = weight_at_800 * 0.699
    
    # Get corresponding value from Run Log
    # Sheet name is likely the Run ID
    clean_sheet_name = sheet.strip()
    
    # Look up in map
    run_metal_val = residual_map.get(clean_sheet_name)
    
    if run_metal_val is not None:
        results.append({
            'Run_ID': clean_sheet_name,
            'TGA_Fe_wt_pct': fe_equiv,
            'Run_Log_Residual_Metal_wt_pct': run_metal_val
        })
    else:
        print(f"Warning: Run ID {clean_sheet_name} found in TGA but not in Run Log map.")

# Convert to DataFrame
df_comp = pd.DataFrame(results)

if df_comp.empty:
    raise ValueError("No matching data found between TGA sheets and Run Log.")

# 3. Plot Scatter
fig, ax = plt.subplots(figsize=(8, 8))

ax.scatter(
    df_comp['Run_Log_Residual_Metal_wt_pct'], 
    df_comp['TGA_Fe_wt_pct'], 
    s=100, 
    alpha=0.7, 
    edgecolors='k', 
    color='steelblue',
    label='배치 데이터'
)

# Add y=x baseline
lims = [
    min(df_comp['Run_Log_Residual_Metal_wt_pct'].min(), df_comp['TGA_Fe_wt_pct'].min()) - 0.5,
    max(df_comp['Run_Log_Residual_Metal_wt_pct'].max(), df_comp['TGA_Fe_wt_pct'].max()) + 0.5
]
ax.plot(lims, lims, 'r--', linewidth=1.5, label='y = x 기준선')

# Formatting
ax.set_xlabel('런로그 잔류금속 (wt%)', fontsize=12)
ax.set_ylabel('TGA 잔류량 환산 Fe (wt%)', fontsize=12)
ax.set_title('TGA 분석값(Fe 환산) vs 런로그 기록 비교', fontsize=14)
ax.legend(loc='upper left')
ax.grid(True, linestyle=':', alpha=0.6)

# Set aspect ratio equal to make visual inspection easier
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'tga_vs_runlog_scatter.png'), dpi=300)
plt.close()
