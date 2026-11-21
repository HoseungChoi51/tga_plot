import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Load Downtime Data
downtime_path = "data/downtime.xlsx"
df_downtime = pd.read_excel(downtime_path, sheet_name='정지이력')

# Parse dates and calculate week number based on the rule: March 2 is Week 1
# The prompt states: "주차는 3월 2일(월)이 1주차예요."
start_date = pd.Timestamp('2026-03-02')

def get_week_number(date_str):
    try:
        # Handle various date formats if necessary, assuming standard Excel date parsing works
        current_date = pd.to_datetime(date_str)
        delta_days = (current_date - start_date).days
        if delta_days < 0:
            return None
        # Week 1 starts at day 0. 
        # Day 0-6 -> Week 1
        # Day 7-13 -> Week 2
        week_num = int(np.floor(delta_days / 7)) + 1
        return week_num
    except Exception:
        return None

df_downtime['주차'] = df_downtime['일자'].apply(get_week_number)
df_downtime = df_downtime.dropna(subset=['주차'])

# Convert downtime minutes to hours
df_downtime['정지시간_시간단위'] = df_downtime['정지시간(분)'] / 60.0

# Group by week to get total downtime hours per week
weekly_downtime = df_downtime.groupby('주차')['정지시간_시간단위'].sum().reset_index()
weekly_downtime.rename(columns={'정지시간_시간단위': '총정지시간(h)'}, inplace=True)

# 2. Load Run Log Summary Data
run_log_path = "data/run_log.xlsx"
df_weekly_summary = pd.read_excel(run_log_path, sheet_name='주간요약')

# Check if the column name matches exactly. Preview says: A 주차, G 총생산량(kg)
# Ensure numeric types
df_weekly_summary['주차'] = pd.to_numeric(df_weekly_summary['주차'], errors='coerce')
df_weekly_summary['총생산량(kg)'] = pd.to_numeric(df_weekly_summary['총생산량(kg)'], errors='coerce')

# Merge the two datasets on '주차'
merged_df = pd.merge(weekly_downtime, df_weekly_summary, on='주차', how='inner')

# Filter valid data points for plotting
plot_df = merged_df.dropna(subset=['총정지시간(h)', '총생산량(kg)'])

if plot_df.empty:
    print("No data available to plot.")
else:
    # 3. Create Scatter Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_data = plot_df['총정지시간(h)']
    y_data = plot_df['총생산량(kg)']
    
    ax.scatter(x_data, y_data, color='#1f77b4', alpha=0.7, edgecolors='w', s=80)
    
    # Add labels and title
    ax.set_xlabel('주차별 총 정지시간 (h)', fontsize=12)
    ax.set_ylabel('주차별 총생산량 (kg)', fontsize=12)
    ax.set_title('주차별 총 정지시간과 총생산량의 관계', fontsize=14)
    
    # Optional: Add trend line to visualize correlation
    if len(plot_df) > 1:
        coeffs = np.polyfit(x_data, y_data, 1)
        poly = np.poly1d(coeffs)
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = poly(x_line)
        ax.plot(x_line, y_line, '--', color='red', label=f'선형 추이 (기울기={coeffs[0]:.2f})')
        ax.legend()

    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Save figure
    output_filename = os.path.join(OUT_DIR, 'downtime_vs_production_scatter.png')
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    plt.close(fig)
    print(f"Plot saved to {output_filename}")
