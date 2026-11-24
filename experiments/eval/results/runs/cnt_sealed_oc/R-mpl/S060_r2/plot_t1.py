import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# Ensure date column is datetime
df['일자'] = pd.to_datetime(df['일자'])

# Filter for June-August 2026
start_date = '2026-06-01'
end_date = '2026-08-30'
mask = (df['일자'] >= start_date) & (df['일자'] <= end_date)
df_filtered = df[mask]

# Group by reactor and sum downtime minutes
downtime_by_reactor = df_filtered.groupby('반응기')['정지시간(분)'].sum()

# Calculate total downtime for percentage
total_downtime = downtime_by_reactor.sum()

# Prepare data for pie chart
labels = downtime_by_reactor.index.tolist()
sizes = downtime_by_reactor.values.tolist()

# Create pie chart
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Pastel1.colors)

# Add title
ax.set_title(f'{start_date} ~ {end_date} 반응기별 정지 시간 비율\n(총 정지 시간: {total_downtime:.0f} 분)', fontsize=14)

# Equal aspect ratio ensures that pie is drawn as a circle
ax.axis('equal')

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "downtime_pie_jun_aug.png")
plt.savefig(output_path, dpi=300)
plt.close()
