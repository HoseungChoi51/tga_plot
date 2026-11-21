import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data from Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Filter rows where grade is 'A' or 'B' (passing grades)
# Calculate total runs per reactor and passing runs per reactor
total_runs_per_reactor = df.groupby('반응기').size()
passing_runs_per_reactor = df[df['등급'].isin(['A', 'B'])].groupby('반응기').size()

# Reindex to ensure all reactors are present even if some have no passing runs (though unlikely in this context)
passing_runs_per_reactor = passing_runs_per_reactor.reindex(total_runs_per_reactor.index, fill_value=0)

# Calculate pass rate (%)
pass_rate_percentage = (passing_runs_per_reactor / total_runs_per_reactor) * 100

# Prepare data for plotting
reactors = pass_rate_percentage.index.tolist()
rates = pass_rate_percentage.values.tolist()

# Create bar plot
fig, ax = plt.subplots(figsize=(8, 6))
bars = ax.bar(reactors, rates, color='steelblue', edgecolor='black')

# Add labels and title
ax.set_xlabel('반응기')
ax.set_ylabel('합격률 (%)')
ax.set_title('반응기별 합격률 (A·B 등급 비율)')
ax.set_ylim(0, 100) # Pass rate is percentage, max 100

# Add value labels on top of each bar
for bar, rate in zip(bars, rates):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{rate:.1f}%',
            ha='center', va='bottom', fontsize=10)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_file = os.path.join(OUT_DIR, "reactor_pass_rate.png")
plt.savefig(output_file, dpi=300)
plt.close()
