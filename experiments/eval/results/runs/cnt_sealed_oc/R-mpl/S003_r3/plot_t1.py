import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configure environment
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
df_downtime = pd.read_excel("data/downtime.xlsx", sheet_name="정지이력")

# Convert date column to datetime for filtering
df_downtime['일자'] = pd.to_datetime(df_downtime['일자'])

# Filter data: June 1st to August 30th
start_date = '2026-06-01'
end_date = '2026-08-30'
mask = (df_downtime['일자'] >= start_date) & (df_downtime['일자'] <= end_date)
df_filtered = df_downtime[mask]

# Count occurrences by cause ('원인')
counts = df_filtered['원인'].value_counts()

# If no data in the range, handle gracefully or just plot empty? 
# Assuming there is data based on preview range ending Aug 30.
labels = counts.index.tolist()
sizes = counts.values.tolist()

# Create pie chart
fig, ax = plt.subplots(figsize=(8, 8))

# Define hatch patterns and gray colors for black/white printing compatibility
hatches = ['///', '\\\\\\', 'xxx', '...', '|||', '+++', '---']
colors = ['#ffffff', '#dddddd', '#bbbbbb', '#999999', '#777777', '#555555', '#333333']

# Ensure we have enough hatches/colors if more categories exist than predefined
while len(hatches) < len(labels):
    hatches.append('...') # default fallback pattern
while len(colors) < len(labels):
    colors.append('#ffffff')

wedges, texts, autotexts = ax.pie(
    sizes, 
    labels=labels, 
    autopct='%1.1f%%', 
    startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(edgecolor='black', linewidth=1),
    hatch=hatches[:len(labels)] if len(hatches) >= len(labels) else [h % len(hatches) for h in range(len(labels))] # Simple logic to repeat if needed, though value_counts usually small
)

# Apply colors manually to wedges to ensure contrast with hatches if needed, 
# but for B/W report, distinct hatches + edge color is key. 
# The 'colors' parameter in pie sets face color. 
# Let's re-create with explicit facecolors for better control over grayscale.
ax.clear()

wedges, texts, autotexts = ax.pie(
    sizes, 
    labels=labels, 
    autopct='%1.1f%%', 
    startangle=90,
    pctdistance=0.75,
    colors=colors[:len(labels)], # Use grayscale shades
    hatch=[hatches[i % len(hatches)] for i in range(len(labels))],
    wedgeprops=dict(edgecolor='black', linewidth=1.5)
)

# Adjust text properties for visibility on grayscale/hatched background
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')
    
for text in texts:
    text.set_fontsize(12)

ax.set_title(f"설비 정지 원인별 비율 ({start_date} ~ {end_date})", fontsize=14, pad=20)

# Add a legend instead of cluttered labels if preferred, but request asked for percentage display.
# Labels are already in pie. 

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "downtime_pie_chart_bw.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close()
