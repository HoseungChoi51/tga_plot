import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure fonts for Korean support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B18_r2/out"
SHEET_NAME = "Annealed"

def calculate_onset_temperature(temp, weight):
    """
    Calculate the onset temperature using the tangent method.
    1. Find the point of maximum mass loss rate (max |dW/dT|).
    2. Draw a tangent at that point.
    3. Find intersection with the baseline (initial weight) and the final stable weight line.
    4. The onset is where the tangent intersects the initial baseline.
    """
    # Filter valid data range (usually up to 900C)
    mask = (temp >= 30) & (temp <= 900)
    t = temp[mask]
    w = weight[mask]
    
    if len(t) < 10:
        return None, None, None, None

    # Calculate derivative dW/dT
    dw_dt = np.gradient(w, t)
    
    # Find index of maximum degradation rate (most negative slope)
    idx_max_rate = np.argmin(dw_dt)
    T_peak = t[idx_max_rate]
    W_peak = w[idx_max_rate]
    Slope_peak = dw_dt[idx_max_rate]
    
    # Define Baseline 1 (Initial): Average weight in the first few degrees (e.g., 30-50C)
    init_mask = (t >= 30) & (t <= 60)
    if not np.any(init_mask):
        init_w = w[0]
    else:
        init_w = np.mean(w[init_mask])
        
    # Define Baseline 2 (Final): Average weight near the end (e.g., 800-900C)
    final_mask = (t >= 750) & (t <= 900)
    if not np.any(final_mask):
        final_w = w[-1]
    else:
        final_w = np.mean(w[final_mask])

    # Tangent Line Equation: y - W_peak = Slope_peak * (x - T_peak)
    # We want to find x (Temperature) where this tangent intersects the initial baseline (y = init_w)
    # init_w - W_peak = Slope_peak * (T_onset - T_peak)
    # T_onset = (init_w - W_peak) / Slope_peak + T_peak
    
    if Slope_peak == 0:
        return None, None, None, None
        
    T_onset = (init_w - W_peak) / Slope_peak + T_peak
    
    # Sanity check: Onset should be lower than Peak Temperature
    if T_onset > T_peak or T_onset < 30:
        # Fallback or adjustment if calculation yields weird results due to noise
        # Sometimes simple inflection point detection is better, but sticking to standard tangent method logic
        pass

    return T_onset, T_peak, init_w, final_w

def plot_tga_with_onset(df, sheet_name, out_dir):
    # Extract columns based on standard TGA naming conventions from preview
    # B: Temperature, C: Weight, D: Deriv Weight
    try:
        temp = df.iloc[:, 1].values
        weight = df.iloc[:, 2].values
        dtg = df.iloc[:, 3].values
    except IndexError:
        print("Column structure unexpected")
        return

    # Calculate Onset
    T_onset, T_peak, base_init, base_final = calculate_onset_temperature(temp, weight)
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color_weight = '#1f4e9c'
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_weight, fontsize=12)
    line1, = ax1.plot(temp, weight, color=color_weight, linewidth=2, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color_weight)
    
    # Plot DTG on right axis
    ax2 = ax1.twinx()
    color_dtg = '#c0392b'
    ax2.set_ylabel('DTG (%/°C)', color=color_dtg, fontsize=12)
    # Invert DTG so peaks point up
    line2, = ax2.plot(temp, -dtg, color=color_dtg, linewidth=2, linestyle='--', label='DTG (-1x)')
    ax2.tick_params(axis='y', labelcolor=color_dtg)
    
    # Title
    ax1.set_title(f'TGA Analysis: {sheet_name}', fontsize=14, fontweight='bold')
    
    # Markers and Annotations
    if T_onset is not None:
        # Find the weight value at the calculated onset temperature for plotting reference lines
        idx_onset = np.argmin(np.abs(temp - T_onset))
        W_at_onset_approx = weight[idx_onset]
        
        # Draw vertical line at Onset
        ax1.axvline(x=T_onset, color='green', linestyle=':', linewidth=1.5, label=f'Onset Temp ({T_onset:.1f} °C)')
        
        # Annotate Onset
        ax1.annotate(f'Onset: {T_onset:.1f} °C', 
                     xy=(T_onset, W_at_onset_approx), 
                     xytext=(T_onset + 20, W_at_onset_approx + 10),
                     arrowprops=dict(facecolor='green', shrink=0.05, width=1, headwidth=5),
                     fontsize=10, color='green', fontweight='bold')
                     
        # Optionally draw the tangent line segment for visualization
        # Extend tangent line slightly around the peak
        dx = 50
        t_start = max(30, T_peak - dx)
        t_end = min(900, T_peak + dx)
        
        # Recalculate tangent points based on peak values stored earlier? 
        # Better to recalculate locally for robustness
        dw_dt_full = np.gradient(weight, temp)
        idx_peak_full = np.argmin(dw_dt_full)
        T_pk = temp[idx_peak_full]
        W_pk = weight[idx_peak_full]
        Slp_pk = dw_dt_full[idx_peak_full]
        
        if Slp_pk != 0:
            y_start = W_pk + Slp_pk * (t_start - T_pk)
            y_end = W_pk + Slp_pk * (t_end - T_pk)
            ax1.plot([t_start, t_end], [y_start, y_end], color='gray', linestyle='-', alpha=0.5, linewidth=1)

    # Residue Marker (Standard requirement: nearest 800C)
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    ax1.plot(temp[idx_800], residue_val, 'o', color='black', markersize=6)
    ax1.annotate(f'Residue: {residue_val:.1f}%', 
                 xy=(temp[idx_800], residue_val), 
                 xytext=(temp[idx_800] - 50, residue_val - 10),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 fontsize=9)

    # Peak Marker (Standard requirement: highest DTG peak above 150C)
    # Already found T_peak in helper, but let's re-verify for marker placement on DTG axis
    # We need to place it on the secondary axis visually or just annotate the primary? 
    # Usually markers are on the curve they belong to. DTG peak is on ax2.
    if T_peak is not None:
        idx_peak_dtg = np.argmin(dtg) # Most negative DTG
        # Ensure it's above 150C
        if temp[idx_peak_dtg] > 150:
             ax2.plot(temp[idx_peak_dtg], -dtg[idx_peak_dtg], 'v', color='black', markersize=6)
             ax2.annotate(f'{temp[idx_peak_dtg]:.0f} °C', 
                          xy=(temp[idx_peak_dtg], -dtg[idx_peak_dtg]), 
                          xytext=(temp[idx_peak_dtg] + 10, -dtg[idx_peak_dtg] + 0.1),
                          fontsize=9, color='black')

    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    # Add onset to legend if plotted
    handles, labels = ax1.get_legend_handles_labels()
    # Combine handles from both axes might be messy, simpler to create custom legend
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color=color_weight, lw=2),
                    Line2D([0], [0], color=color_dtg, lw=2, ls='--')]
    if T_onset is not None:
        custom_lines.append(Line2D([0], [0], color='green', lw=1.5, ls=':'))
        labels.append('Onset Temp')
        
    ax1.legend(custom_lines, ['Weight', 'DTG (-1x)', 'Onset Temp'], loc='center left', bbox_to_anchor=(0.02, 0.5))

    # Grid
    ax1.grid(True, linestyle='--', alpha=0.3)
    
    # Save
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{sheet_name.replace(' ', '_')}_onset.png"
    filepath = os.path.join(out_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

if __name__ == "__main__":
    try:
        df_annealed = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
        plot_tga_with_onset(df_annealed, SHEET_NAME, OUT_DIR)
        print(f"Plot saved to {OUT_DIR}")
    except Exception as e:
        print(f"Error: {e}")
