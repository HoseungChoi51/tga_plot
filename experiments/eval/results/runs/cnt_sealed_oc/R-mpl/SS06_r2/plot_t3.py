import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configure Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Find all Raman CSV files in the data/raman folder
data_dir = "data/raman"
csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))

if not csv_files:
    print("No CSV files found in data/raman")
else:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Define vertical line positions and styles
    v_lines_x = [1350, 1580]
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        label = os.path.splitext(filename)[0]
        
        try:
            df = pd.read_csv(filepath)
            
            # Identify columns robustly
            if 'Raman Shift (cm-1)' in df.columns and 'Intensity (a.u.)' in df.columns:
                x_col = 'Raman Shift (cm-1)'
                y_col = 'Intensity (a.u.)'
            else:
                x_col = df.columns[0]
                y_col = df.columns[1]
            
            shifts = df[x_col].values
            intensities = df[y_col].values
            
            # Filter for G-band region to find max intensity for normalization
            # G band defined as 1550-1620 cm-1
            mask_g_band = (shifts >= 1550) & (shifts <= 1620)
            
            if np.any(mask_g_band):
                g_max_intensity = np.max(intensities[mask_g_band])
                if g_max_intensity > 0:
                    normalized_intensities = intensities / g_max_intensity
                else:
                    normalized_intensities = intensities
            else:
                normalized_intensities = intensities
            
            # Filter plot data to 1200-1700 cm-1 range
            mask_plot_range = (shifts >= 1200) & (shifts <= 1700)
            
            plot_x = shifts[mask_plot_range]
            plot_y = normalized_intensities[mask_plot_range]
            
            # Determine color based on filename prefix
            is_r4 = label.startswith("R4")
            
            if is_r4:
                color = 'red'
                linewidth = 1.5
                alpha = 0.9
                linestyle = '-'
            else:
                color = 'gray'
                linewidth = 1.0
                alpha = 0.6
                linestyle = '--'
                
            ax.plot(plot_x, plot_y, label=label, color=color, linewidth=linewidth, alpha=alpha, linestyle=linestyle)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Add vertical dashed lines at specified Raman shifts
    for x_val in v_lines_x:
        ax.axvline(x=x_val, color='black', linestyle=':', linewidth=1.0, alpha=0.7)
        # Optional: Add text labels near the top of the lines
        ax.text(x_val + 5, 0.95, f"{x_val}", rotation=90, va='top', ha='left', fontsize=8, color='black')

    # Set plot properties
    ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
    ax.set_ylabel("Normalized Intensity (G-band max = 1)", fontsize=12)
    ax.set_title("Raman Spectra Overlay (1200–1700 cm⁻¹, G-band Normalized)", fontsize=14)
    
    # Ensure limits match the requested range exactly for clarity
    ax.set_xlim(1200, 1700)
    
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_path = os.path.join(OUT_DIR, "raman_overlay_normalized_styled.png")
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")
