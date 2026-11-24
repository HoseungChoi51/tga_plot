import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure environment for Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

def load_raman_data(filepath, sheet_name):
    # Read CSV with default settings; handle potential decimal commas if necessary via float_precision or replace
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='cp949')
    
    # If the file uses semicolons and decimal commas (as mentioned in general instructions), we might need to detect it.
    # The preview says standard CSV columns A and B. Let's assume standard comma-separated first.
    # If headers are in Korean or specific format, we look for numeric columns.
    
    # Identify X and Y columns based on typical Raman data structure
    # Preview shows: A Raman Shift (cm-1) | B Intensity (a.u.)
    cols = df.columns.tolist()
    x_col = None
    y_col = None
    
    for c in cols:
        if 'Shift' in str(c) or 'Wavenumber' in str(c) or 'cm-1' in str(c) or c == cols[0]:
            x_col = c
        elif 'Intensity' in str(c) or 'Signal' in str(c) or c == cols[1]:
            y_col = c
            
    if x_col is None: x_col = cols[0]
    if y_col is None: y_col = cols[1]
    
    df = df[[x_col, y_col]].dropna()
    df.columns = ['wavenumber', 'intensity']
    return df

def baseline_correction(df):
    """
    Subtracts a straight line defined by averaging intensity at 
    1100 +/- 10 cm^-1 and 1800 +/- 10 cm^-1.
    """
    wn = df['wavenumber'].values
    int_val = df['intensity'].values
    
    # Define windows
    w_left_min, w_left_max = 1090, 1110
    w_right_min, w_right_max = 1790, 1810
    
    # Mask for points in windows
    mask_left = (wn >= w_left_min) & (wn <= w_left_max)
    mask_right = (wn >= w_right_min) & (wn <= w_right_max)
    
    # Calculate mean intensities in these windows
    if np.sum(mask_left) > 0:
        avg_left = np.mean(int_val[mask_left])
        center_left = np.mean(wn[mask_left])
    else:
        # Fallback if no points found exactly, use nearest? 
        # Given high resolution (1560 pts over 2000 cm-1 -> ~1.3 cm-1/pt), points should exist.
        avg_left = np.interp(1100, wn, int_val)
        center_left = 1100
        
    if np.sum(mask_right) > 0:
        avg_right = np.mean(int_val[mask_right])
        center_right = np.mean(wn[mask_right])
    else:
        avg_right = np.interp(1800, wn, int_val)
        center_right = 1800
        
    # Create linear function: y = m*x + c
    # Two points: (center_left, avg_left) and (center_right, avg_right)
    slope = (avg_right - avg_left) / (center_right - center_left)
    intercept = avg_left - slope * center_left
    
    # Subtract baseline
    baseline = slope * wn + intercept
    corrected_int = int_val - baseline
    
    # Ensure no negative values before normalization if strictly required, 
    # but usually correction allows slight negatives which are then handled in G-band max norm.
    # We keep raw corrected values for now.
    
    df_corrected = df.copy()
    df_corrected['corrected_intensity'] = corrected_int
    return df_corrected

def normalize_g_band(df, g_min=1550, g_max=1620):
    """
    Normalize such that the maximum value of the corrected intensity in the G band range becomes 1.
    """
    wn = df['wavenumber'].values
    corr_int = df['corrected_intensity'].values
    
    mask_g = (wn >= g_min) & (wn <= g_max)
    
    if np.sum(mask_g) == 0:
        return df # Cannot normalize
    
    max_g_val = np.max(corr_int[mask_g])
    
    if max_g_val == 0:
        df['normalized_intensity'] = 0
    else:
        df['normalized_intensity'] = corr_int / max_g_val
        
    return df

# File paths from preview
files_info = [
    ("data/raman/R1-260326-1.csv", "R1"),
    ("data/raman/R2-260616-1.csv", "R2"),
    ("data/raman/R4-260721-1.csv", "R4")
]

plot_data = []

for fpath, label in files_info:
    try:
        df_raw = load_raman_data(fpath, "") # Sheet name logic simplified as csvs don't have sheets usually, or single sheet.
        
        # 1. Baseline Correction
        df_corr = baseline_correction(df_raw)
        
        # 2. Normalize to G-band max = 1
        df_norm = normalize_g_band(df_corr)
        
        plot_data.append((label, df_norm))
    except Exception as e:
        print(f"Error processing {fpath}: {e}")

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#d62728'] # Blue, Orange, Red

for i, (label, df) in enumerate(plot_data):
    # Filter for 1000-2000 cm-1 range
    mask_range = (df['wavenumber'] >= 1000) & (df['wavenumber'] <= 2000)
    df_plot = df[mask_range]
    
    ax.plot(df_plot['wavenumber'], df_plot['normalized_intensity'], 
            label=f"{label}", color=colors[i], linewidth=1.5)

ax.set_xlabel('Raman Shift (cm⁻¹)', fontsize=12)
ax.set_ylabel('Normalized Intensity (a.u.)', fontsize=12)
ax.set_title('Baseline-corrected and G-band normalized Raman spectra', fontsize=14)
ax.legend(loc='best')
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_xlim(1000, 2000)
ax.set_ylim(bottom=-0.1) # Allow slight negative if baseline subtraction went below zero, though max is 1

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "raman_normalized_overlay.png")
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Plot saved to {save_path}")
