import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read all sheets
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    
    tga_series = []
    dtga_series = []
    
    colors = ['#5470c6', '#91cc75', '#fac858'] # Default ECharts colors or similar
    
    for i, sheet_name in enumerate(sheets):
        df = pd.read_excel(xl, sheet_name=sheet_name)
        
        # Clean column names if necessary based on preview
        # Assuming columns are: 'Time (min)', 'Temperature (°C)', 'Weight (%)', 'Deriv. Weight (%/°C)'
        temp_col = 'Temperature (°C)'
        weight_col = 'Weight (%)'
        deriv_col = 'Deriv. Weight (%/°C)'
        
        # Extract data
        temps = df[temp_col].tolist()
        weights = df[weight_col].tolist()
        derivs = df[deriv_col].tolist()
        
        # Prepare TGA series (Weight %) - Y axis 0
        tga_series.append({
            "name": f"{sheet_name} TGA",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temps, weights)],
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "color": colors[i % len(colors)]
            },
            "itemStyle": {
                "color": colors[i % len(colors)]
            }
        })
        
        # Prepare DTGA series (Deriv. Weight) - Y axis 1
        dtga_series.append({
            "name": f"{sheet_name} DTGA",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(temps, derivs)],
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "type": "dashed", # Distinguish DTGA from TGA visually
                "color": colors[i % len(colors)]
            },
            "itemStyle": {
                "color": colors[i % len(colors)]
            }
        })

    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": None # Keep default JSON serializable structure
        },
        "legend": {
            "orient": "vertical",
            "right": 10,
            "top": "middle",
            "data": [s["name"] for s in tga_series + dtga_series],
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
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
            "scale": True,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 100,
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed"
                    }
                }
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "position": "right",
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": tga_series + dtga_series
    }

    output = {
        "figures": [
            {
                "name": "plot1",
                "option": option,
                "width": 800,
                "height": 600,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
