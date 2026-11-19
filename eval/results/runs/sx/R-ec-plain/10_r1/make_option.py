import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def main():
    # Read all sheets from the Excel file
    xls = pd.ExcelFile(DATA_FILE)
    
    figures = []
    
    # Define colors for different samples
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # Prepare data for each sheet
    series_weight = []
    series_dtg = []
    legend_data = []
    
    for idx, sheet_name in enumerate(xls.sheet_names):
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Extract columns based on the preview structure
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dtg_col = 'D.W(%/C)'
        
        # Get temperature and weight data
        temps = df[temp_col].tolist()
        weights = df[weight_col].tolist()
        dtgs = df[dtg_col].tolist()
        
        # Find residual weight at 700°C
        # Find the index closest to 700°C
        target_temp = 700.0
        if len(temps) > 0:
            # Find the closest temperature point to 700
            min_diff = float('inf')
            closest_idx = 0
            for i, t in enumerate(temps):
                diff = abs(t - target_temp)
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = i
            
            residual_weight = round(weights[closest_idx], 2)
            
            # Create label with residual weight info
            display_name = f"{sheet_name} (Residual @700°C: {residual_weight}%)"
        else:
            display_name = sheet_name
        
        legend_data.append(display_name)
        
        # Weight loss curve series
        series_weight.append({
            "name": display_name,
            "type": "line",
            "data": [[t, w] for t, w in zip(temps, weights)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[idx % len(colors)]}
        })
        
        # DTG curve series (on secondary y-axis)
        series_dtg.append({
            "name": f"DTG - {display_name}",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(temps, dtgs)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 1.5, "type": "dashed"},
            "itemStyle": {"color": colors[idx % len(colors)]}
        })
    
    # Combine all series
    all_series = series_weight + series_dtg
    
    option = {
        "title": {
            "text": "TGA / DTG Analysis",
            "left": "center",
            "top": "2%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
            }
        },
        "tooltip": {
            "trigger": "axis",
            "formatter": "{a}<br/>Temp: {b} °C<br/>Value: {c}",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": legend_data + [f"DTG - {ln}" for ln in legend_data],
            "bottom": "2%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            }
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "15%",
            "top": "12%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 30,
            "max": 900,
            "axisLabel": {
                "formatter": "{value} °C"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {"type": "dashed"}
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 45,
                "min": 0,
                "max": 100,
                "position": "left",
                "axisLabel": {
                    "formatter": "{value} %"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {"type": "dashed"}
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 45,
                "position": "right",
                "axisLabel": {
                    "formatter": "{value}"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": all_series
    }
    
    figure = {
        "name": "tga_dtg_plot",
        "option": option,
        "width": 800,
        "height": 600,
        "dpi": 300,
        "formats": ["png"]
    }
    
    output = {"figures": [figure]}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
