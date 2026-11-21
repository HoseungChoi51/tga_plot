import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 1. Setup Environment and Fonts
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 2. Load Data
# Load Run Log
try:
    df_run_log = pd.read_excel("data/run_log.xlsx", sheet_name="런로그")
except Exception as e:
    print(f"Error reading run log: {e}")
    exit()

# Clean column names in run log to handle potential whitespace issues causing KeyError
df_run_log.columns = df_run_log.columns.str.strip()

# Load TGA Batches (all sheets)
tga_data = {}
try:
    xl_file = pd.ExcelFile("data/tga_batches.xlsx")
    for sheet in xl_file.sheet_names:
        # Read each sheet
        df_tga_sheet = pd.read_excel(xl_file, sheet_name=sheet)
        tga_data[sheet] = df_tga_sheet
except Exception as e:
    print(f"Error reading TGA batches: {e}")
    exit()

# 3. Process Data
results = []

for run_id, df_tga in tga_data.items():
    # Check if this run_id exists in the run log
    # Ensure types match (usually string vs string)
    mask = df_run_log['런ID'].astype(str).str.strip() == str(run_id).strip()
    
    if not mask.any():
        continue
        
    run_info = df_run_log[mask].iloc[0]
    
    # Find columns from TGA sheet robustly
    temp_col = None
    weight_col = None
    
    for col in df_tga.columns:
        col_str = str(col).strip()
        if '온도' in col_str:
            temp_col = col
        if '중량' in col_str and '미분' not in col_str:
            weight_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    # Extract Residual Weight at 800 °C
    target_temp = 800.0
    
    # Sort by temperature just in case
    df_tga_sorted = df_tga.sort_values(by=temp_col)
    
    temps = df_tga_sorted[temp_col].values
    weights = df_tga_sorted[weight_col].values
    
    # Linear interpolation between points surrounding 800°C
    residual_weight_pct = np.nan
    
    if len(temps) > 1:
        below_idx = np.where(temps <= target_temp)[0]
        above_idx = np.where(temps >= target_temp)[0]
        
        if len(below_idx) > 0 and len(above_idx) > 0:
            i_below = below_idx[-1]
            i_above = above_idx[0]
            
            t1, w1 = temps[i_below], weights[i_below]
            t2, w2 = temps[i_above], weights[i_above]
            
            if t2 != t1:
                ratio = (target_temp - t1) / (t2 - t1)
                residual_weight_pct = w1 + ratio * (w2 - w1)
            else:
                residual_weight_pct = w1
        elif len(below_idx) > 0:
            residual_weight_pct = weights[below_idx[-1]]
        elif len(above_idx) > 0:
            residual_weight_pct = weights[above_idx[0]]
    
    if np.isnan(residual_weight_pct):
        continue

    # Convert Residual Weight (Fe2O3) to Fe mass fraction
    calculated_fe_wt_pct = residual_weight_pct * 0.699
    
    # Get Run Log Metal Content
    # The column name in the preview is 'S 잔류금속 (wt%)'. 
    # After stripping spaces, it might be '잔류금속 (wt%)' or similar.
    # We look for a column containing '잔류금속'
    metal_col_name = None
    for col in df_run_log.columns:
        if '잔류금속' in col:
            metal_col_name = col
            break
            
    if metal_col_name is None:
        continue
        
    run_log_metal_wt_pct = run_info[metal_col_name]
    
    results.append({
        'RunID': run_id,
        'TGA_Calc_Fe_wt%': calculated_fe_wt_pct,
        'RunLog_Metal_wt%': run_log_metal_wt_pct
    })

# Create DataFrame for plotting
if not results:
    print("No matching runs found between TGA sheets and Run Log.")
else:
    df_compare = pd.DataFrame(results)
    
    # 4. Plotting
    fig, ax = plt.subplots(figsize=(10, 8))
    
    x_vals = df_compare['RunLog_Metal_wt%']
    y_vals = df_compare['TGA_Calc_Fe_wt%']
    
    # Scatter plot
    scatter = ax.scatter(x_vals, y_vals, s=100, alpha=0.7, edgecolors='k', label='Batch Data')
    
    # Add labels for points
    for i, txt in enumerate(df_compare['RunID']):
        ax.annotate(txt, (x_vals.iloc[i], y_vals.iloc[i]), xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Y = X reference line
    min_val = min(x_vals.min(), y_vals.min()) * 0.9
    max_val = max(x_vals.max(), y_vals.max()) * 1.1
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='y = x')
    
    # Formatting
    ax.set_xlabel('런로그 잔류금속 (wt%)', fontsize=12)
    ax.set_ylabel('TGA 계산 Fe 함량 (wt%) [잔량×0.699]', fontsize=12)
    ax.set_title('TGA 잔류량 기반 Fe 환산값과 런로그 금속함량 비교', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle=':', alpha=0.6)
    
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    
    # Save figure
    output_path = os.path.join(OUT_DIR, "tga_vs_runlog_metal_scatter.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    print(f"Plot saved to {output_path}")
