import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILES = ["/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv", "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt"]
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B05_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(8, 6))

def load_data(filepath):
    # Try reading with different separators for .txt files
    if filepath.endswith('.txt'):
        try:
            df = pd.read_csv(filepath, sep='\t')
            if len(df.columns) < 2:
                df = pd.read_csv(filepath, sep=r'\s+')
        except Exception:
            try:
                df = pd.read_csv(filepath, sep=',')
            except Exception:
                df = pd.read_csv(filepath, sep=';')
    else:
        df = pd.read_csv(filepath)
        
    # Normalize column names to match expected keys from preview
    col_map = {}
    for c in df.columns:
        c_lower = str(c).lower()
        if 'temperature' in c_lower:
            col_map[c] = 'Temperature (°C)'
        elif 'weight' in c_lower and ('deriv' not in c_lower and 'dtg' not in c_lower):
            col_map[c] = 'Weight (%)'
        elif 'deriv' in c_lower or 'dtg' in c_lower:
            col_map[c] = 'Deriv. Weight (%/°C)'
            
    df = df.rename(columns=col_map)
    
    # Drop rows where essential columns are NaN
    required_cols = ['Temperature (°C)', 'Weight (%)', 'Deriv. Weight (%/°C)']
    if all(col in df.columns for col in required_cols):
        df = df.dropna(subset=required_cols)
        
    return df

df_a = load_data(DATA_FILES[0])
df_b = load_data(DATA_FILES[1])

temp_a = df_a["Temperature (°C)"].values
weight_a = df_a["Weight (%)"].values
dtg_a = df_a["Deriv. Weight (%/°C)"].values * -1  # Invert DTG so peaks point up

temp_b = df_b["Temperature (°C)"].values
weight_b = df_b["Weight (%)"].values
dtg_b = df_b["Deriv. Weight (%/°C)"].values * -1

# Plot Lot A
ax1.plot(temp_a, weight_a, color='#1f4e9c', label='Lot A Weight')
ax2 = ax1.twinx()
ax2.plot(temp_a, dtg_a, color='#c0392b', linestyle='--', label='Lot A DTG')

# Plot Lot B
ax1.plot(temp_b, weight_b, color='#2ca02c', label='Lot B Weight')
ax2.plot(temp_b, dtg_b, color='#d35400', linestyle='--', label='Lot B DTG')

# Labels and Titles
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12) 
ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12) 

plt.title('TGA Comparison: Lot A vs Lot B', fontsize=14)

# Residue and Peak Markers Function
def get_residue_and_peak(temp, weight, dtg_inverted):
    if len(temp) == 0:
        return None, None, None, None
        
    # Residue: nearest to 800 C
    idx_res = np.argmin(np.abs(temp - 800))
    res_val = weight[idx_res]
    res_temp = temp[idx_res]
    
    # Peak: highest DTG (positive now) above 150 C
    mask = temp > 150
    if not np.any(mask):
        return res_val, res_temp, None, None
    
    dtg_masked = dtg_inverted[mask]
    temp_masked = temp[mask]
    
    # Filter out NaNs in masked data just in case
    valid_idx = ~np.isnan(dtg_masked)
    if not np.any(valid_idx):
         return res_val, res_temp, None, None
         
    dtg_valid = dtg_masked[valid_idx]
    temp_valid = temp_masked[valid_idx]
    
    idx_max = np.argmax(dtg_valid)
    peak_temp = temp_valid[idx_max]
    peak_dtg_val = dtg_valid[idx_max]
    
    return res_val, res_temp, peak_temp, peak_dtg_val

res_a, res_t_a, peak_t_a, peak_v_a = get_residue_and_peak(temp_a, weight_a, dtg_a)
res_b, res_t_b, peak_t_b, peak_v_b = get_residue_and_peak(temp_b, weight_b, dtg_b)

# Add markers for Lot A
if res_a is not None:
    ax1.plot(res_t_a, res_a, 'o', color='#1f4e9c', markersize=8)
    ax1.annotate(f'Residue {res_a:.1f}%', xy=(res_t_a, res_a), xytext=(10, -15), textcoords='offset points', color='#1f4e9c', fontsize=10)

if peak_t_a is not None:
    ax2.plot(peak_t_a, peak_v_a, 'v', color='#c0392b', markersize=8)
    ax2.annotate(f'{peak_t_a:.0f} °C', xy=(peak_t_a, peak_v_a), xytext=(10, 10), textcoords='offset points', color='#c0392b', fontsize=10)

# Add markers for Lot B
if res_b is not None:
    ax1.plot(res_t_b, res_b, 's', color='#2ca02c', markersize=8)
    ax1.annotate(f'Residue {res_b:.1f}%', xy=(res_t_b, res_b), xytext=(10, 15), textcoords='offset points', color='#2ca02c', fontsize=10)

if peak_t_b is not None:
    ax2.plot(peak_t_b, peak_v_b, '^', color='#d35400', markersize=8)
    ax2.annotate(f'{peak_t_b:.0f} °C', xy=(peak_t_b, peak_v_b), xytext=(10, -15), textcoords='offset points', color='#d35400', fontsize=10)


# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
all_lines = lines_1 + lines_2
all_labels = labels_1 + labels_2

legend = ax1.legend(all_labels, loc='center left', bbox_to_anchor=(0.05, 0.5), frameon=False)

plt.tight_layout()

out_path = os.path.join(OUT_DIR, "TGA_overlay.png")
plt.savefig(out_path, dpi=300)
plt.close()
