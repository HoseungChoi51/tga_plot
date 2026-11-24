import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Configure Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Find all Raman CSV files in the data/raman folder
data_dir = "data/raman"
csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

if not csv_files:
    print("No CSV files found in data/raman")
else:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for filepath in sorted(csv_files):
        filename = os.path.basename(filepath)
        # Extract a label from the filename (e.g., R1-260326-1)
        label = os.path.splitext(filename)[0]
        
        try:
            # Read the CSV file
            # Based on preview, columns are 'Raman Shift (cm-1)' and 'Intensity (a.u.)'
            df = pd.read_csv(filepath)
            
            # Check if columns match expected names or use positional indexing
            if 'Raman Shift (cm-1)' in df.columns and 'Intensity (a.u.)' in df.columns:
                x_col = 'Raman Shift (cm-1)'
                y_col = 'Intensity (a.u.)'
            else:
                # Fallback to first two columns if headers differ slightly
                x_col = df.columns[0]
                y_col = df.columns[1]
            
            # Plot the spectrum
            ax.plot(df[x_col], df[y_col], label=label, linewidth=1.0, alpha=0.8)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Set plot properties
    ax.set_xlabel("Raman Shift (cm⁻¹)", fontsize=12)
    ax.set_ylabel("Intensity (a.u.)", fontsize=12)
    ax.set_title("Raman Spectra Overlay", fontsize=14)
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    # Save figure
    output_path = os.path.join(OUT_DIR, "raman_overlay.png")
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")
