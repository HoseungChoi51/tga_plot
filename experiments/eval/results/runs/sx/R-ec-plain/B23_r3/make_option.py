import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
    
    # Define colors for each sample
    colors = {
        "Raw": "#000000",
        "Acid-washed": "#1f77b4",  # Blue
        "Annealed": "#d62728"      # Red
    }
    
    series_list = []
    
    for sheet_name in ["Raw", "Acid-washed", "Annealed"]:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Identify columns based on preview
        temp_col = "Temperature (°C)"
        weight_col = "Weight (%)"
        deriv_col = "Deriv. Weight (%/°C)"
        
        # Prepare data for TGA (Weight %) - y-axis 0
        # Format: [[x, y], ...]
        tga_data = df[[temp_col, weight_col]].dropna().values.tolist()
        
        # Prepare data for DTG (Deriv. Weight %) - y-axis 1
        dtg_data = df[[temp_col, deriv_col]].dropna().values.tolist()
        
        color = colors[sheet_name]
        
        # Add TGA series (left y-axis)
        series_list.append({
            "name": f"{sheet_name} TGA",
            "type": "line",
            "yAxisIndex": 0,
            "data": tga_data,
            "showSymbol": False,
            "lineStyle": {"color": color, "width": 2},
            "itemStyle": {"color": color}
        })
        
        # Add DTG series (right y-axis)
        series_list.append({
            "name": f"{sheet_name} DTG",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "lineStyle": {"color": color, "width": 2, "type": "dashed"},
            "itemStyle": {"color": color}
        })

    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": [
                "Raw TGA", "Raw DTG",
                "Acid-washed TGA", "Acid-washed DTG",
                "Annealed TGA", "Annealed DTG"
            ],
            "top": 10
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 0,
            "max": 950
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 110
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "position": "right",
                "min": -1.5,
                "max": 0.5
            }
        ],
        "series": series_list
    }

    result = {
        "figures": [
            {
                "name": "tga_comparison",
                "option": option,
                "width": 800,
                "height": 500,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
