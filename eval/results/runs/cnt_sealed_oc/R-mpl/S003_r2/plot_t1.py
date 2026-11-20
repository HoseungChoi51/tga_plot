import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# Parse date column
# The preview says '일자' contains dates like 2026-03-02. 
# We need to ensure it's datetime type for filtering.
if not np.issubdtype(df['일자'].dtype, np.datetime64):
    df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# Filter data: June 1st to August 30th (Year is likely 2026 based on preview, but we filter by month/day range if year isn't specified strictly, 
# however the request implies a specific period. Given the preview shows 2026, we assume 2026 or just filter months 6-8 within the available range.
# To be safe and match "June 1 to Aug 30", we filter by date range.
start_date = pd.Timestamp('2026-06-01')
end_date = pd.Timestamp('2026-08-30')

# Filter rows where date is within range
mask = (df['일자'] >= start_date) & (df['일자'] <= end_date)
df_filtered = df[mask]

# Count occurrences per cause ('원인')
counts = df_filtered['원인'].value_counts()

# If no data in this range, fallback to checking if years are different or just using all data if range is empty?
# The prompt says "make a reasonable choice". If the range is empty, the chart will be empty. 
# Let's check if there is any data at all first.
if counts.empty:
    # Maybe try without year constraint if dates are just strings that failed parsing? 
    # Or maybe the user meant 2025? But preview says 2026. 
    # Let's stick to the logic. If empty, we still plot what we have (empty pie).
    pass

# Prepare labels and values
labels = counts.index.tolist()
values = counts.values.tolist()

# Create grayscale colormap or manual gray tones + hatching
n_items = len(labels)
# Generate gray shades from dark to light
grays = [str(x/100) for x in np.linspace(20, 90, n_items)] 

fig, ax = plt.subplots(figsize=(10, 8))

# Draw pie chart with hatching patterns for distinction in B&W printing
hatches = ['/', '\\', '|', '-', '+', 'x', '*', '.', 'o']
wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                  colors=grays, hatch=[hatches[i % len(hatches)] for i in range(n_items)],
                                  startangle=90, counterclock=False)

# Style adjustments for better visibility of hatches and black borders
for w, h in zip(wedges, [hatches[i % len(hatches)] for i in range(n_items)]):
    w.set_hatch(h)
    w.set_edgecolor('black')
    w.set_linewidth(1.5)

# Ensure text is readable
for text in texts + autotexts:
    text.set_fontsize(12)
    text.set_color('black')

ax.set_title(f"설비 정지 원인별 비율\n({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})", fontsize=16, pad=20)

# Equal aspect ratio ensures that pie is drawn as a circle
ax.axis('equal')

# Save figure
output_filename = os.path.join(OUT_DIR, "downtime_pie_chart_jun_aug.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
