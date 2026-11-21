import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Sheet names to plot
    sheets = ["PE", "PVC", "PET"]
    
    # Colors for each polymer
    colors = {
        "PE": "#5470C6",
        "PVC": "#91CC75",
        "PET": "#FAC858"
    }
    
    tga_series = []
    dtg_series = []
    
    # Process each sheet
    for sheet_name in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Clean data: drop NaN rows just in case
        df = df.dropna(subset=["Temperature (°C)", "Weight (%)", "Deriv. Weight (%/°C)"])
        
        temp = df["Temperature (°C)"].tolist()
        weight = df["Weight (%)"].tolist()
        deriv_weight = df["Deriv. Weight (%/°C)"].tolist()
        
        # TGA Series (Weight %)
        tga_series.append({
            "name": f"{sheet_name} TGA",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temp, weight)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": colors[sheet_name]
            },
            "itemStyle": {
                "color": colors[sheet_name]
            }
        })
        
        # DTG Series (Deriv. Weight %/°C)
        dtg_series.append({
            "name": f"{sheet_name} DTG",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[t, dw] for t, dw in zip(temp, deriv_weight)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": colors[sheet_name],
                "type": "dashed"
            },
            "itemStyle": {
                "color": colors[sheet_name]
            }
        })

    # Combine series
    all_series = tga_series + dtg_series
    
    # ECharts Option
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": "{a}: ({b}, {c})"
        },
        "legend": {
            "orient": "vertical",
            "right": "5%",
            "top": "center",
            "data": [s["name"] for s in all_series]
        },
        "grid": {
            "left": "3%",
            "right": "15%", # Space for legend on the right
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 30,
            "max": 900
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 100
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "position": "right",
                "offset": 0
            }
        ],
        "series": all_series
    }

    result = {
        "figures": [
            {
                "name": "polymers_tga_dtg",
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
