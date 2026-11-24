import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# File path based on preview
file_path = "data/raman/R4-260407-1.csv"

# Read the CSV file
# The preview indicates columns: 'A Raman Shift (cm-1)' and 'B Intensity (a.u.)'
# We need to check if there are any specific formatting issues (like semicolons or decimal commas mentioned in general instructions),
# but usually standard CSVs use commas. Let's try reading with default settings first, handling potential index column if present.
try:
    df = pd.read_csv(file_path)
except Exception as e:
    # If default fails, maybe it's a different delimiter or encoding
    try:
        df = pd.read_csv(file_path, sep=';', decimal=',')
    except:
        raise e

# Clean up column names if they have leading/trailing spaces or special characters from Excel export
df.columns = df.columns.str.strip()

# Identify X and Y columns
# Based on preview: A is Raman Shift, B is Intensity
x_col = None
y_col = None

for col in df.columns:
    if "Raman Shift" in col:
        x_col = col
    elif "Intensity" in col:
        y_col = col

if x_col is None or y_col is None:
    # Fallback: assume first numeric column is X, second is Y if headers aren't clear
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) >= 2:
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
    else:
        raise ValueError("Could not identify Raman Shift and Intensity columns")

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(df[x_col], df[y_col], color='blue', linewidth=1)

# Labels and Title
plt.xlabel(x_col)
plt.ylabel(y_col)
plt.title(f'Raman Spectrum: {os.path.basename(file_path)}')

# Grid
plt.grid(True, linestyle='--', alpha=0.5)

# Save plot
output_filename = os.path.join(OUT_DIR, "R4-260407-1_raman_spectrum.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
