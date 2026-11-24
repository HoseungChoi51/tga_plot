```python
import os
import json
import math
import numpy as np
import pandas as pd

DATA_FILE = os.environ.get("DATA_FILE", "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx")
TARGET_SHEET = "1006R1-V normal"

# Read target sheet, fallback to first sheet if needed
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names
sheet = TARGET_SHEET if TARGET_SHEET in sheet_names else sheet_names[0]
df = xl.parse(sheet)

cols = list(df.columns)

# User asked for B, C, D columns as x, y1, y2.
if len(cols) >= 4:
    x_col, y1_col, y2_col = cols[1], cols[2], cols[3]
elif len(cols) == 3:
    x_col, y1_col, y2_col = cols[0], cols[1], cols[2]
else:
    x_col, y1_col, y2_col = cols[0], cols[-2], cols[-1]

x = pd.to_numeric(df[x_col], errors="coerce").astype(float)
y1 = pd.to_numeric(df[y1_col], errors="coerce").astype(float)
y2 = pd.to_numeric(df[y2_col], errors="coerce").astype(float)

mask = x.notna() & y1.notna() & y2.notna()
x = x[mask].to_numpy()
y1 = y1[mask].to_numpy()
y2 = y2[mask].to_numpy()

order = np.argsort(x)
x = x[order]
y1 = y1[order]
y2 = y2[order]

# Standard TGA convention: plot DTG multiplied by -1 so peaks point upward.
y2_plot = -y2

series_weight = [
    [round(float(a), 3), round(float(b), 3)]
    for a, b in zip(x, y1)
]

series_dtg = [
    [round(float(a), 3), round(float(b), 5)]
    for a, b in zip(x, y2_plot)
]

# Residue: weight at the measured temperature nearest 800 °C.
res_idx = int(np.argmin(np.abs(x - 800.0)))
res_x = float(x[res_idx])
res_y = float(y1[res_idx])
res_label = f"Residue {res_y:.1f}%"

# Peak: highest plotted DTG peak above 150 °C.
# The label includes the temperature and the plotted peak value, because the user asked for the DTG max value.
peak_mask = x > 150.0
if np.any(peak_mask):
    peak_x_arr = x[peak_mask]
    peak_y_arr = y2_plot[peak_mask]
    peak_local_idx = int(np.argmax(peak_y_arr))
    peak_x = float(peak