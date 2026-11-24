import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
df = pd.read_excel("data/run_log.xlsx", sheet_name="런로그")

# Clean column names: strip whitespace to handle potential hidden spaces in headers
df.columns = df.columns.str.strip()

# Identify columns based on cleaned names
humidity_col = '외기습도 (%)'
yield_col = 'CNT수율 (g/g-cat)'
igid_col = 'IG/ID'
grade_col = '등급 (A/B/C)'

# Verify columns exist after stripping
if humidity_col not in df.columns or yield_col not in df.columns or igid_col not in df.columns or grade_col not in df.columns:
    # Fallback: try to find columns by partial match if exact match fails due to weird spacing
    cols = df.columns.tolist()
    def find_col(keyword):
        for c in cols:
            if keyword in c:
                return c
        raise ValueError(f"Column containing '{keyword}' not found in {cols}")
    
    humidity_col = find_col('외기습도')
    yield_col = find_col('CNT수율')
    igid_col = find_col('IG/ID')
    grade_col = find_col('등급')

# Drop rows with missing values in relevant columns
df_clean = df.dropna(subset=[humidity_col, yield_col, igid_col, grade_col]).copy()

# Create a numeric grade score for correlation analysis (A=3, B=2, C=1)
grade_map = {'A': 3, 'B': 2, 'C': 1}
df_clean['등급_점수'] = df_clean[grade_col].map(grade_map)

# --- Plot 1: Scatter plots of Humidity vs Yield and IG/ID with trend lines ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Scatter: Humidity vs CNT Yield
ax1 = axes[0]
scatter1 = ax1.scatter(df_clean[humidity_col], df_clean[yield_col], 
                       c=df_clean['등급_점수'], cmap='viridis', alpha=0.6, edgecolors='k', s=50)
ax1.set_xlabel('외기습도 (%)')
ax1.set_ylabel('CNT수율 (g/g-cat)')
ax1.set_title('습도 vs CNT 수율')

# Add linear regression line
slope, intercept, r_value, p_value, std_err = stats.linregress(df_clean[humidity_col], df_clean[yield_col])
x_line = np.linspace(df_clean[humidity_col].min(), df_clean[humidity_col].max(), 100)
y_line = slope * x_line + intercept
ax1.plot(x_line, y_line, color='red', linestyle='--', label=f'선형 회귀 (R²={r_value**2:.3f})')
ax1.legend()

# Annotate correlation coefficient
ax1.text(0.05, 0.95, f'상관계수: {r_value:.3f}\nP-value: {p_value:.4f}', 
         transform=ax1.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

# Scatter: Humidity vs IG/ID
ax2 = axes[1]
scatter2 = ax2.scatter(df_clean[humidity_col], df_clean[igid_col], 
                       c=df_clean['등급_점수'], cmap='viridis', alpha=0.6, edgecolors='k', s=50)
ax2.set_xlabel('외기습도 (%)')
ax2.set_ylabel('IG/ID')
ax2.set_title('습도 vs IG/ID 비율')

# Add linear regression line
slope2, intercept2, r_value2, p_value2, std_err2 = stats.linregress(df_clean[humidity_col], df_clean[igid_col])
y_line2 = slope2 * x_line + intercept2
ax2.plot(x_line, y_line2, color='red', linestyle='--', label=f'선형 회귀 (R²={r_value2**2:.3f})')
ax2.legend()

# Annotate correlation coefficient
ax2.text(0.05, 0.95, f'상관계수: {r_value2:.3f}\nP-value: {p_value2:.4f}', 
         transform=ax2.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "humidity_vs_quality_scatter.png"), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 2: Box plot of Quality Metrics by Humidity Bins ---
# Define humidity bins
bins = [0, 40, 60, 80, 100]
labels = ['저습도\n(<40%)', '중습도\n(40-60%)', '고습도\n(60-80%)', '초고습도\n(>80%)']
df_clean['습도구간'] = pd.cut(df_clean[humidity_col], bins=bins, labels=labels, right=False)

# Ensure the category order is correct for plotting
df_clean['습도구간'] = df_clean['습도구간'].cat.reorder_categories(labels)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Boxplot: Humidity Bin vs CNT Yield
ax1 = axes[0]
# Groupby ensures we get groups in the categorical order
groups_yield = df_clean.groupby('습도구간')[yield_col]
box_data_yield = [group.values for name, group in groups_yield]
bp1 = ax1.boxplot(box_data_yield, labels=labels, patch_artist=True)
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
for patch, color in zip(bp1['boxes'], colors):
    patch.set_facecolor(color)
ax1.set_xlabel('습도 구간')
ax1.set_ylabel('CNT수율 (g/g-cat)')
ax1.set_title('습도 구간에 따른 CNT 수율 분포')
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Boxplot: Humidity Bin vs IG/ID
ax2 = axes[1]
groups_igid = df_clean.groupby('습도구간')[igid_col]
box_data_igid = [group.values for name, group in groups_igid]
bp2 = ax2.boxplot(box_data_igid, labels=labels, patch_artist=True)
for patch, color in zip(bp2['boxes'], colors):
    patch.set_facecolor(color)
ax2.set_xlabel('습도 구간')
ax2.set_ylabel('IG/ID')
ax2.set_title('습도 구간에 따른 IG/ID 비율 분포')
ax2.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "humidity_bin_boxplots.png"), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 3: Grade Distribution by Humidity Bin (Stacked Bar Chart) ---
fig, ax = plt.subplots(figsize=(10, 6))

# Cross-tabulate humidity bins and grades
cross_tab = pd.crosstab(df_clean['습도구간'], df_clean[grade_col])
# Ensure all grades are present
for g in ['A', 'B', 'C']:
    if g not in cross_tab.columns:
        cross_tab[g] = 0
cross_tab = cross_tab[['A', 'B', 'C']] # Order A, B, C

# Normalize to percentages for stacked bar
cross_tab_pct = cross_tab.div(cross_tab.sum(axis=1), axis=0) * 100

# Plot stacked bar
bottom = np.zeros(len(cross_tab_pct))
colors_grade = {'A': '#2ecc71', 'B': '#f1c40f', 'C': '#e74c3c'}

# Get index as list of strings to avoid issues with categorical types in some mpl versions
x_labels = [str(l) for l in cross_tab_pct.index]

for grade in ['A', 'B', 'C']:
    values = cross_tab_pct[grade].values
    bars = ax.bar(x_labels, values, bottom=bottom, label=f'{grade}급', color=colors_grade[grade], edgecolor='black')
    bottom += values
    
    # Add percentage text inside bars
    for i, v in enumerate(values):
        if v > 5: # Only show text if segment is large enough
            ax.text(i, bottom[i] - v/2, f'{v:.1f}%', ha='center', va='center', color='white', fontweight='bold')

ax.set_xlabel('습도 구간')
ax.set_ylabel('비율 (%)')
ax.set_title('습도 구간에 따른 품질 등급 분포')
ax.legend(title='품질 등급', loc='upper left')
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "humidity_grade_distribution.png"), dpi=300, bbox_inches='tight')
plt.close()

print(f"Plots saved to {OUT_DIR}")
