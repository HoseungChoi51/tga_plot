import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to remove potential whitespace or hidden characters
df.columns = df.columns.str.strip()

# Identify the grade column dynamically since exact name might vary slightly in header vs preview description
grade_col = None
for col in df.columns:
    if '등급' in str(col):
        grade_col = col
        break

if grade_col is None:
    raise ValueError("Could not find grade column in the dataframe.")

# Calculate grade composition percentage per reactor
# Group by reactor and grade, count occurrences
grade_counts = df.groupby(['반응기', grade_col]).size().reset_index(name='count')

# Pivot to get reactors as rows and grades as columns
pivot_df = grade_counts.pivot(index='반응기', columns=grade_col, values='count').fillna(0)

# Ensure all grades A, B, C are present in columns
for grade in ['A', 'B', 'C']:
    if grade not in pivot_df.columns:
        pivot_df[grade] = 0

# Reorder columns to ensure A, B, C order
pivot_df = pivot_df[['A', 'B', 'C']]

# Calculate total runs per reactor
total_runs = pivot_df.sum(axis=1)

# Calculate percentage for each grade
percentage_df = pivot_df.div(total_runs, axis=0) * 100

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

reactors = percentage_df.index.tolist()
grades = ['A', 'B', 'C']
colors = ['#2ecc71', '#f1c40f', '#e74c3c']  # Green for A, Yellow for B, Red for C

bottoms = [0] * len(reactors)

for i, grade in enumerate(grades):
    values = percentage_df[grade].values
    bars = ax.bar(reactors, values, bottom=bottoms, label=f'Grade {grade}', color=colors[i], edgecolor='black', linewidth=0.5)
    
    # Add text labels on bars
    for j, val in enumerate(values):
        if val > 0:  # Only add text if value is significant enough to see
            y_pos = bottoms[j] + val / 2
            ax.text(j, y_pos, f'{val:.1f}%', ha='center', va='center', fontsize=9, color='white' if grade == 'A' else 'black')
    
    bottoms = [b + v for b, v in zip(bottoms, values)]

ax.set_title('반응기별 등급 구성비 (%)', fontsize=14, pad=15)
ax.set_xlabel('반응기', fontsize=12)
ax.set_ylabel('구성비 (%)', fontsize=12)
ax.set_ylim(0, 100)
ax.legend(title='등급', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "reactor_grade_composition.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
