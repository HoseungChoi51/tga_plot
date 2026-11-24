import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Filter valid reactors and grades
valid_reactors = ['R1', 'R2', 'R3', 'R4']
valid_grades = ['A', 'B', 'C']

# Clean data: keep only rows with valid reactor and grade
df_clean = df_runs[df_runs['반응기'].isin(valid_reactors) & df_runs['등급'].isin(valid_grades)].copy()

# Calculate counts per reactor and grade
counts = df_clean.groupby(['반응기', '등급']).size().unstack(fill_value=0)

# Reorder columns to ensure A, B, C order
grade_order = ['A', 'B', 'C']
if all(g in counts.columns for g in grade_order):
    counts = counts[grade_order]

# Calculate percentages (row-wise normalization to sum to 100%)
total_counts = counts.sum(axis=1)
percentages = counts.div(total_counts, axis=0) * 100

# Prepare data for plotting
reactors = percentages.index.tolist()
x_pos = range(len(reactors))
width = 0.6  # Width of the bars

# Colors for grades
colors = {'A': '#2ecc71', 'B': '#f1c40f', 'C': '#e74c3c'}

fig, ax = plt.subplots(figsize=(8, 6))

# Plot stacked bar chart
bottom = [0] * len(reactors)
for grade in grade_order:
    if grade in percentages.columns:
        values = percentages[grade].values
        ax.bar(x_pos, values, width, bottom=bottom, label=f'등급 {grade}', color=colors[grade])
        
        # Add percentage text on top of each segment
        for i, v in enumerate(values):
            if v > 5:  # Only add text if segment is large enough
                y_text = bottom[i] + v / 2
                ax.text(x_pos[i], y_text, f'{v:.1f}%', ha='center', va='center', fontsize=9, color='black')
        
        bottom += values

# Customize plot
ax.set_xticks(x_pos)
ax.set_xticklabels(reactors)
ax.set_ylabel('구성비 (%)')
ax.set_title('반응기별 등급(A/B/C) 구성비')
ax.set_ylim(0, 100)
ax.legend(title='등급', loc='upper left', bbox_to_anchor=(1, 1))
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Tight layout to prevent label cutoff
plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "reactor_grade_composition.png")
plt.savefig(output_file, dpi=300)
plt.close()
