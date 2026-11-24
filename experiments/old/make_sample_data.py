"""Create sample_tga.xlsx: synthetic CNT TGA runs (air, 10 °C/min) for testing."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(0)

def run(steps, residue, sign=-1, tmax=900):
    T = np.arange(30, tmax + 0.5, 0.5)
    time = (T - 30) / 10.0                      # min, at 10 °C/min
    rate = np.zeros_like(T)                     # %/°C lost
    for amount, center, width in steps:         # each step: Gaussian DTG peak
        rate += amount * np.exp(-0.5 * ((T - center) / width) ** 2) / (width * np.sqrt(2 * np.pi))
    total = sum(s[0] for s in steps)
    W = 100 - np.cumsum(rate) * 0.5
    W = residue + (W - W.min()) * (100 - residue) / (100 - W.min()) if total else W
    D = np.gradient(W, T) + rng.normal(0, 0.002, T.size)
    W = W + rng.normal(0, 0.02, T.size)
    return pd.DataFrame({"Time (min)": time, "Temperature (°C)": T,
                         "Weight (%)": W, "D.W (%/°C)": D if sign < 0 else -D})

sheets = {
    "Pristine MWCNT": run([(2, 90, 20), (88, 600, 35)], residue=8),
    "Acid-treated MWCNT": run([(4, 95, 20), (12, 400, 30), (80, 560, 40)], residue=3),
    "CNT-Fe catalyst": run([(1.5, 85, 15), (9, 380, 30), (70, 520, 30)], residue=22),
    # DTG stored as a positive number (some instruments do this)
    "Positive DTG export": run([(2, 90, 20), (90, 640, 30)], residue=5, sign=+1),
}
with pd.ExcelWriter("sample_tga.xlsx") as xw:
    for name, df in sheets.items():
        df.to_excel(xw, sheet_name=name, index=False)
print("wrote sample_tga.xlsx")
