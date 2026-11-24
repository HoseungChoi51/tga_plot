import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuration
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# Clean column names just in case there are spaces or weird chars (though preview looks clean)
df.columns = df.columns.str.strip()

# Ensure '일자' is datetime
df['일자'] = pd.to_datetime(df['일자'])

# Filter for June–August 2026 (2026-06-01 to 2026-08-30)
start_date = pd.Timestamp('2026-06-01')
end_date = pd.Timestamp('2026-08-30')
mask = (df['일자'] >= start_date) & (df['일자'] <= end_date)
df_filtered = df[mask].copy()

# Calculate total downtime minutes per reactor
downtime_by_reactor = df_filtered.groupby('반응기')['정지시간(분)'].sum().reset_index()

# Prepare data for pie chart
labels = downtime_by_reactor['반응기']
sizes = downtime_by_reactor['정지시간(분)']

# Create the plot
fig, ax = plt.subplots(figsize=(8, 8))

# Plot pie chart
# autopct='%1.1f%%' shows percentage
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, counterclock=False)

# Title and label
ax.set_title("June–August 2026 Downtime Share by Reactor", fontsize=14)

# Adjust text sizes if needed
for autotext in autotexts:
    autotext.set_fontsize(12)

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "downtime_pie_jun_aug.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close(fig)
