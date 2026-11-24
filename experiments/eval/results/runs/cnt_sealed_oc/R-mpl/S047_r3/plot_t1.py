import pandas as pd
import matplotlib.pyplot as plt
import os
import traceback

# Configuration
OUT_DIR = "out/t1"
DATA_FILE = "data/run_log.xlsx"
SHEET_NAME = "런로그"

def main():
    try:
        # Ensure output directory exists
        if not os.path.exists(OUT_DIR):
            os.makedirs(OUT_DIR)
        
        # Set font for Korean text support
        # Note: If 'Noto Sans CJK KR' is not found by matplotlib, it might fall back or error.
        # We ensure the rcParams are set before plotting.
        plt.rcParams["font.family"] = "Noto Sans CJK KR"
        plt.rcParams["axes.unicode_minus"] = False

        # Read Excel file
        df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
        
        # Debug print to confirm data loading
        print(f"Data loaded. Shape: {df.shape}")
        print(df.head())
        
        # Ensure '일자' is datetime type
        # The column name in preview is 'B 일자 (yyyy-mm-dd)', so we look for a column containing '일자'
        date_col = [c for c in df.columns if '일자' in str(c)][0]
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Identify columns based on preview patterns
        reactor_col = [c for c in df.columns if '반응기' in str(c)][0]
        prod_rate_col = [c for c in df.columns if '생산속도' in str(c)][0]
        run_time_col = [c for c in df.columns if '가동시간' in str(c)][0]
        
        # Calculate production per run in kg
        # Formula: 생산속도 (g/h) * 가동시간 (h) / 1000 = Production (kg)
        df['생산량_kg'] = (df[prod_rate_col] * df[run_time_col]) / 1000
        
        # Group by Date and Reactor to sum up production for that day per reactor
        daily_prod = df.groupby([date_col, reactor_col])['생산량_kg'].sum().reset_index()
        
        # Pivot table to have one column per reactor for easier plotting
        pivot_df = daily_prod.pivot(index=date_col, columns=reactor_col, values='생산량_kg')
        
        # Fill NaN with 0 because if a reactor didn't produce on a specific day, its contribution is 0
        pivot_df = pivot_df.fillna(0)
        
        # Sort index to ensure chronological order
        pivot_df = pivot_df.sort_index()
        
        # Reindex to cover all dates from min to max to ensure continuous cumulative sum
        full_range = pd.date_range(start=pivot_df.index.min(), end=pivot_df.index.max())
        pivot_df = pivot_df.reindex(full_range).fillna(0)
        
        # Calculate Cumulative Sum for each reactor
        cumulative_df = pivot_df.cumsum()
        
        # Plotting
        fig, ax = plt.subplots(figsize=(12, 7))
        
        reactors = cumulative_df.columns.tolist()
        
        for reactor in reactors:
            ax.plot(cumulative_df.index, cumulative_df[reactor], label=f'{reactor}', linewidth=2)
        
        # Formatting
        ax.set_title('Cumulative Production per Reactor (Daily Resolution)', fontsize=14)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Cumulative Production (kg)', fontsize=12)
        ax.legend(title='Reactor', loc='upper left')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Format x-axis dates nicely
        fig.autofmt_xdate(rotation=45)
        
        # Save plot
        output_path = os.path.join(OUT_DIR, "cumulative_production_per_reactor.png")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        print(f"Plot successfully saved to {output_path}")
        
        plt.close(fig)
        
    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
