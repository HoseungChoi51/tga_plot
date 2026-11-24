import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 1. Load Run Log to get '잔류금속 (wt%)' for each Run ID
run_log_path = "data/run_log.xlsx"
df_runs = pd.read_excel(run_log_path, sheet_name="런로그")

# Identify the correct column name for Residual Metal.
# The preview shows headers like 'S 잔류금속 (wt%)'. 
# Sometimes spaces or encoding issues cause mismatches. We search for a column containing '잔류금속'.
metal_col = None
for col in df_runs.columns:
    if '잔류금속' in str(col):
        metal_col = col
        break

if metal_col is None:
    # Fallback to index S (column 18, 0-indexed 18? Let's check preview: A=0... S=18)
    # Preview says S is '잔류금속 (wt%)'. 
    # If header row was parsed correctly, it should be there. If not, maybe we need positional.
    # But let's assume strict matching failed due to whitespace. We strip columns.
    df_runs.columns = [str(c).strip() for c in df_runs.columns]
    for col in df_runs.columns:
        if '잔류금속' in col:
            metal_col = col
            break

# Create a mapping from Run ID to Residual Metal Content
if metal_col:
    run_metal_map = df_runs.set_index("런ID")[metal_col].to_dict()
else:
    raise ValueError("Could not find '잔류금속' column in run log.")

# 2. Load TGA Batches and calculate Fe content from residue at 800°C
tga_file_path = "data/tga_batches.xlsx"
tga_data = []

xls = pd.ExcelFile(tga_file_path)
sheet_names = xls.sheet_names

for sheet in sheet_names:
    # Read TGA data for this batch
    df_tga = pd.read_excel(tga_file_path, sheet_name=sheet)
    
    cols = df_tga.columns
    
    # Robustly find temperature and weight columns
    temp_col = None
    weight_col = None
    
    for c in cols:
        c_str = str(c)
        if "온도" in c_str:
            temp_col = c
        elif "중량" in c_str and "미분" not in c_str:
            weight_col = c
            
    if temp_col is None or weight_col is None:
        # Fallback to positional indices based on preview structure
        # Col 0: Time, Col 1: Temp, Col 2: Weight, Col 3: Derivative
        temp_idx = 1
        weight_idx = 2
        temp_col = cols[temp_idx]
        weight_col = cols[weight_idx]

    # Filter data around 800°C to find the residue value
    target_temp = 800.0
    df_tga['temp_diff'] = abs(df_tga[temp_col] - target_temp)
    closest_row_idx = df_tga['temp_diff'].idxmin()
    
    residue_wt_pct = df_tga.loc[closest_row_idx, weight_col]
    
    # Convert Oxide residue (Fe2O3) to Fe content
    # Factor given: 0.699
    fe_content_wt_pct = residue_wt_pct * 0.699
    
    run_id = sheet
    
    # Get corresponding residual metal from Run Log
    if run_id in run_metal_map:
        log_metal = run_metal_map[run_id]
    else:
        log_metal = np.nan
        
    tga_data.append({
        "Run_ID": run_id,
        "Residue_800C_Fe_Wt_Pct": fe_content_wt_pct,
        "Log_Residual_Metal_Wt_Pct": log_metal
    })

df_comparison = pd.DataFrame(tga_data)

# Drop rows with NaN values for plotting clarity
df_plot = df_comparison.dropna(subset=["Residue_800C_Fe_Wt_Pct", "Log_Residual_Metal_Wt_Pct"])

# 3. Plot Scatter
fig, ax = plt.subplots(figsize=(8, 8))

ax.scatter(
    df_plot["Residue_800C_Fe_Wt_Pct"], 
    df_plot["Log_Residual_Metal_Wt_Pct"], 
    s=100, 
    alpha=0.7, 
    edgecolors='k', 
    label="TGA 배치 vs 런로그"
)

# Add y=x baseline
limit_min = min(df_plot["Residue_800C_Fe_Wt_Pct"].min(), df_plot["Log_Residual_Metal_Wt_Pct"].min())
limit_max = max(df_plot["Residue_800C_Fe_Wt_Pct"].max(), df_plot["Log_Residual_Metal_Wt_Pct"].max())
pad = (limit_max - limit_min) * 0.05
x_lim = [limit_min - pad, limit_max + pad]

ax.plot(x_lim, x_lim, 'r--', linewidth=2, label="y = x 기준선")

ax.set_xlim(x_lim)
ax.set_ylim(x_lim)

ax.set_xlabel("TGA 잔류량 환산 Fe 함량 (wt%)")
ax.set_ylabel("런로그 기록 잔류금속 (wt%)")
ax.set_title("TGA 측정값과 생산 로그 잔류금속 비교")
ax.legend()
ax.grid(True, linestyle=':', alpha=0.6)

# Save figure
output_path = os.path.join(OUT_DIR, "tga_vs_log_scatter.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
