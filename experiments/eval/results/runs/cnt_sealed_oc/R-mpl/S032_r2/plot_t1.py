import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font for matplotlib
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False  # To display minus signs correctly

# Read the data file
# The file is a CSV with Korean headers. Based on preview, it has columns: A 시각, B 1존(°C), C 2존(°C), D 3존(°C), E 2존 SP(°C)
file_path = "data/r2_zone_temps.csv"
df = pd.read_csv(file_path)

# Clean column names if they have leading/trailing spaces or specific formats from preview description
# Preview says: A 시각 | B 1존(°C) ... E 2존 SP(°C)
# Let's inspect typical pandas read behavior. If headers are just the text, we use them.
# Assuming standard read_csv behavior keeps headers as strings.

time_col = '시각'
zone2_col = '2존(°C)'
sp_col = '2존 SP(°C)'

# Check if columns exist, adjust if necessary (robustness)
if time_col not in df.columns:
    # Try to find a column that looks like time/date
    for col in df.columns:
        if '시간' in col or '시각' in col or 'date' in col.lower() or 'time' in col.lower():
            time_col = col
            break
            
if zone2_col not in df.columns:
    for col in df.columns:
        if '2존' in col and 'SP' not in col.upper():
            zone2_col = col
            break

if sp_col not in df.columns:
    for col in df.columns:
        if '2존' in col and ('SP' in col.upper() or '설정' in col):
            sp_col = col
            break

# Parse datetime
df[time_col] = pd.to_datetime(df[time_col])

# Calculate deviation: Zone 2 Temp - SP
df['deviation'] = df[zone2_col] - df[sp_col]
df['abs_deviation'] = df['deviation'].abs()

# Find the point with maximum absolute deviation
max_dev_idx = df['abs_deviation'].idxmax()
max_dev_time = df.loc[max_dev_idx, time_col]
max_dev_value = df.loc[max_dev_idx, 'deviation']
max_abs_dev_value = df.loc[max_dev_idx, 'abs_deviation']

# Create plot
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(df[time_col], df['deviation'], color='blue', linewidth=0.8, label='2존 온도 편차 (Temp - SP)')

# Highlight the max deviation point
ax.scatter([max_dev_time], [max_dev_value], color='red', s=50, zorder=5, label=f'최대 편차 시점 ({max_abs_dev_value:.2f} °C)')

# Annotate the max deviation point
text_str = f"일시: {max_dev_time.strftime('%Y-%m-%d %H:%M:%S')}\n편차: {max_dev_value:+.2f} °C"
ax.annotate(text_str, 
            xy=(max_dev_time, max_dev_value), 
            xytext=(10, 10), 
            textcoords='offset points', 
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", ec="k", lw=1, alpha=0.8),
            arrowprops=dict(facecolor='black', shrink=0.05))

# Formatting
ax.set_title("R2 반응기 2존 온도 설정값(SP) 대비 편차", fontsize=14)
ax.set_xlabel("시간", fontsize=12)
ax.set_ylabel("온도 편차 (°C)", fontsize=12)
ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
ax.legend(loc='best')
ax.grid(True, linestyle=':', alpha=0.6)

# Adjust layout to prevent label clipping
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "r2_zone2_temp_deviation.png")
plt.savefig(output_filename, dpi=300)
plt.close()

print(f"Plot saved to {output_filename}")
print(f"Maximum deviation occurred at: {max_dev_time}")
print(f"Deviation value: {max_dev_value:.2f} °C")
