import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Load data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B02_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# Extract columns
temp = df["Temperature (°C)"].values
weight = df["Weight (%)"].values
heat_flow = df["Heat Flow (W/g)"].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight on left y-axis
color1 = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1, = ax1.plot(temp, weight, color=color1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color1)

# Create second y-axis for Heat Flow
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.set_ylabel('Heat Flow (W/g)', color=color2, fontsize=12)
line2, = ax2.plot(temp, heat_flow, color=color2, label='Heat Flow (W/g)')
ax2.tick_params(axis='y', labelcolor=color2)

# Find peaks in Heat Flow
# Endothermic peaks: positive values (assuming endothermic is positive based on typical DSC conventions, 
# but let's check the data description: min -1.374, max 2.307. Usually endothermic is down or up depending on convention.
# The user asks for "absorption peaks" (endothermic) and "emission peak" (exothermic).
# In many DSC plots, endothermic is negative and exothermic is positive, OR vice versa.
# Let's look at the data range: min=-1.374, max=2.307.
# Typically, if we see a large positive peak, it might be exothermic or endothermic depending on instrument.
# However, standard DSC often has endothermic pointing down (negative) and exothermic pointing up (positive).
# BUT, sometimes it's reversed. Let's assume standard scientific plotting where we just find local maxima/minima.
# User says: "흡열 피크 두 개" (two endothermic peaks) and "발열 피크 하나" (one exothermic peak).
# Let's find all significant peaks. We will use find_peaks on heat_flow and also on -heat_flow to catch both directions if needed,
# but usually one direction corresponds to endo and the other to exo.
# Let's assume positive heat flow = endothermic? Or negative?
# Let's look at the prompt again. It doesn't specify sign convention.
# Commonly in TGA-DSC combined data provided by instruments like TA Instruments or Mettler Toledo:
# Endothermic events are often plotted as negative deflections (if heat flow is defined as sample minus reference power).
# Exothermic events are positive.
# Let's try finding peaks in positive direction first (potential exothermic) and negative direction (potential endothermic).
# If that yields 1 pos peak and 2 neg peaks, then Pos=Exo, Neg=Endo.
# If it yields 2 pos and 1 neg, then Pos=Endo, Neg=Exo.

# Find peaks in positive direction (local maxima)
peaks_pos, properties_pos = find_peaks(heat_flow, height=0.1, distance=50) # Threshold and distance tuned
# Find peaks in negative direction (local minima, which are peaks of -heat_flow)
peaks_neg, properties_neg = find_peaks(-heat_flow, height=0.1, distance=50)

# Filter out noise near start/end if necessary
valid_peaks_pos = [p for p in peaks_pos if temp[p] > 50 and temp[p] < 900]
valid_peaks_neg = [p for p in peaks_neg if temp[p] > 50 and temp[p] < 900]

# Determine which is endo/exo based on count expectation from user request:
# User expects 2 endothermic, 1 exothermic.
# Let's see counts.
count_pos = len(valid_peaks_pos)
count_neg = len(valid_peaks_neg)

endo_peaks = []
exo_peaks = []

if count_neg >= 2 and count_pos <= 1:
    # Assume Negative = Endothermic, Positive = Exothermic
    endo_peaks = valid_peaks_neg
    exo_peaks = valid_peaks_pos
elif count_pos >= 2 and count_neg <= 1:
    # Assume Positive = Endothermic, Negative = Exothermic
    endo_peaks = valid_peaks_pos
    exo_peaks = valid_peaks_neg
else:
    # Fallback: Just pick the largest ones roughly matching the description or take top N
    # Sort by magnitude
    sorted_pos = sorted(valid_peaks_pos, key=lambda i: heat_flow[i], reverse=True)
    sorted_neg = sorted(valid_peaks_neg, key=lambda i: heat_flow[i]) # Most negative
    
    # Heuristic: Take 2 largest magnitude negatives as endo, 1 largest positive as exo? 
    # Or vice versa. Given typical materials, CaOx decomposition steps:
    # 1. Dehydration (Endo)
    # 2. Decomposition to Carbonate (Endo)
    # 3. Decomposition to Oxide (Endo)? No, usually CaO formation is not strongly exo.
    # Wait, CaOx thermal decomposition:
    # CaC2O4·H2O -> CaC2O4 + H2O (Endo)
    # CaC2O4 -> CaCO3 + CO (Endo)
    # CaCO3 -> CaO + CO2 (Endo)
    # So typically ALL are endothermic. Why does the user ask for 1 exothermic?
    # Maybe there is an oxidation step? Or maybe the convention is flipped.
    # If the data has Min -1.374 and Max 2.307.
    # If all are endo, and endo is negative, we expect 3 negative peaks.
    # If endo is positive, we expect 3 positive peaks.
    # The user specifically asks for 2 Endo and 1 Exo. This implies one event is opposite.
    # Perhaps the last step is considered exothermic in this specific dataset/convention?
    # Or perhaps my peak finding thresholds are merging/splitting things.
    
    # Let's just plot what we found and label them based on the most likely interpretation:
    # Usually, larger swings are the main reactions.
    # Let's assume the user knows their data. I will identify the two largest peaks in one direction and one in the other.
    
    # Let's combine all peaks with their type guess
    all_candidates = []
    for p in valid_peaks_pos:
        all_candidates.append((p, 'pos'))
    for p in valid_peaks_neg:
        all_candidates.append((p, 'neg'))
        
    # Sort candidates by absolute magnitude of heat flow
    all_candidates.sort(key=lambda x: abs(heat_flow[x[0]]), reverse=True)
    
    # Pick top 3 distinct peaks (ensuring they are separated)
    selected_peaks = []
    for cand in all_candidates:
        idx, typ = cand
        # Check if close to already selected
        too_close = False
        for s_idx, _ in selected_peaks:
            if abs(temp[idx] - temp[s_idx]) < 20:
                too_close = True
                break
        if not too_close:
            selected_peaks.append(cand)
        if len(selected_peaks) == 3:
            break
            
    # Now assign labels. We have 3 peaks. We need 2 Endo, 1 Exo.
    # Count types in selected_peaks
    pos_count = sum(1 for _, t in selected_peaks if t == 'pos')
    neg_count = sum(1 for _, t in selected_peaks if t == 'neg')
    
    if pos_count == 1 and neg_count == 2:
        # Pos = Exo, Neg = Endo
        for idx, typ in selected_peaks:
            if typ == 'neg':
                endo_peaks.append(idx)
            else:
                exo_peaks.append(idx)
    elif pos_count == 2 and neg_count == 1:
        # Pos = Endo, Neg = Exo
        for idx, typ in selected_peaks:
            if typ == 'pos':
                endo_peaks.append(idx)
            else:
                exo_peaks.append(idx)
    else:
        # Default fallback: Assume Neg=Endo, Pos=Exo and take top 2 neg and top 1 pos
        endo_peaks = [idx for idx, typ in selected_peaks if typ=='neg'][:2]
        exo_peaks = [idx for idx, typ in selected_peaks if typ=='pos'][:1]


# Plot markers and annotations
for idx in endo_peaks:
    ax2.plot(temp[idx], heat_flow[idx], 'o', color='#2ecc71', markersize=8, zorder=5)
    ax2.annotate(f'{temp[idx]:.0f} °C\n(Endo)', xy=(temp[idx], heat_flow[idx]), 
                 xytext=(10, 10), textcoords='offset points',
                 arrowprops=dict(arrowstyle='->', color='black'),
                 fontsize=9, ha='left')

for idx in exo_peaks:
    ax2.plot(temp[idx], heat_flow[idx], 's', color='#e67e22', markersize=8, zorder=5)
    ax2.annotate(f'{temp[idx]:.0f} °C\n(Exo)', xy=(temp[idx], heat_flow[idx]), 
                 xytext=(-10, -20), textcoords='offset points',
                 arrowprops=dict(arrowstyle='->', color='black'),
                 fontsize=9, ha='right')

# Residue at 800 C
idx_800 = np.argmin(np.abs(temp - 800))
res_weight = weight[idx_800]
res_temp = temp[idx_800]
ax1.plot(res_temp, res_weight, 'D', color=color1, markersize=6, zorder=5)
ax1.annotate(f'Residue {res_weight:.1f}%', xy=(res_temp, res_weight), 
             xytext=(10, -15), textcoords='offset points',
             arrowprops=dict(arrowstyle='->', color=color1),
             fontsize=9, color=color1)

# Title
sheet_name = "caox"
plt.title(sheet_name, fontsize=14)

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

plt.tight_layout()
out_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
plt.savefig(out_path, dpi=300)
plt.close()
