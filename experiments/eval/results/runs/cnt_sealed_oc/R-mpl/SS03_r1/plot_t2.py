import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data from Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Extract month from date column for grouping
# The preview indicated the format is 'yyyy-mm-dd' but the error suggests it might be read as a string literal or mixed.
# We try to convert to datetime, handling errors by ignoring them (setting NaT).
# Then we extract the month. If conversion fails entirely, we might need to parse manually, 
# but usually pd.to_datetime with dayfirst=False works for ISO strings.
# Given the error "Unknown datetime string format... yyyy-mm-dd", it implies some cells might literally contain that string or are malformed.
# Let's force conversion with errors='coerce' and drop invalid dates if necessary, though run logs should have valid dates.
df['일자'] = pd.to_datetime(df['일자'], errors='coerce')

# Filter out rows where date parsing failed (if any)
valid_df = df.dropna(subset=['일자']).copy()

# Create month label
valid_df['월_숫자'] = valid_df['일자'].dt.month
valid_df['월'] = valid_df['월_숫자'].astype(str) + '월'

# Filter rows where grade is 'A' or 'B' (passing grades)
valid_df['is_pass'] = valid_df['등급'].isin(['A', 'B'])

# Calculate total runs and passing runs per reactor per month
grouped_data = valid_df.groupby(['월_숫자', '반응기']).agg(
    total_runs=('is_pass', 'size'),
    passing_runs=('is_pass', 'sum')
).reset_index()

# Calculate pass rate (%)
grouped_data['pass_rate'] = (grouped_data['passing_runs'] / grouped_data['total_runs']) * 100

# Pivot the data to have reactors as columns and months as index for plotting
pivot_df = grouped_data.pivot(index='월_숫자', columns='반응기', values='pass_rate')

# Sort by month number just in case
pivot_df = pivot_df.sort_index()

# Prepare labels for x-axis
months_labels = [f"{int(m)}월" for m in pivot_df.index]

# Prepare data for grouped bar chart
reactors = pivot_df.columns.tolist() # Should be R1, R2, R3, R4 sorted naturally or by appearance

# Define positions for bars
x = np.arange(len(pivot_df))  # label locations
width = 0.2  # width of each bar

fig, ax = plt.subplots(figsize=(12, 7))

# Plot bars for each reactor
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
for i, reactor in enumerate(reactors):
    rates = pivot_df[reactor].values
    rects = ax.bar(x + i * width - width * len(reactors)/2 + width/2, rates, 
                   width, label=reactor, color=colors[i % len(colors)], edgecolor='black')
    
    # Add value labels on top of each bar
    for rect, val in zip(rects, rates):
        height = rect.get_height()
        if not np.isnan(height):
            ax.text(rect.get_x() + rect.get_width()/2., height + 1,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=8)

# Add some text for labelling the axes with titles, etc.
ax.set_xlabel('월')
ax.set_ylabel('합격률 (%)')
ax.set_title('월별 반응기별 합격률')
ax.set_xticks(x)
ax.set_xticklabels(months_labels)
ax.legend(title='반응기', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.set_ylim(0, 105) # Give some headroom for labels

plt.tight_layout()

# Save the figure
output_file = os.path.join(OUT_DIR, "monthly_reactor_pass_rate_grouped.png")
plt.savefig(output_file, dpi=300)
plt.close()
