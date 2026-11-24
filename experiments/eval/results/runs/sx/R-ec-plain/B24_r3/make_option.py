import pandas as pd
import json
import numpy as np

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read the PE sheet
    df = pd.read_excel(file_path, sheet_name="PE")
    
    # Extract columns
    temp_c = df["Temperature (°C)"].values
    weight = df["Weight (%)"].values
    deriv_weight = df["Deriv. Weight (%/°C)"].values
    
    # Convert Temperature from Celsius to Kelvin
    temp_k = temp_c + 273.15
    
    # Prepare data for ECharts
    # TGA usually plots Weight vs Temp and Derivative Weight vs Temp
    # We will create two series: one for Weight (left Y-axis) and one for Deriv Weight (right Y-axis)
    
    # Combine x and y into pairs for scatter or line chart
    # For performance with large datasets, we can sample if needed, but 871 points is fine.
    
    weight_data = [[float(t), float(w)] for t, w in zip(temp_k, weight)]
    deriv_data = [[float(t), float(d)] for t, d in zip(temp_k, deriv_weight)]
    
    option = {
        "backgroundColor": "#ffffff",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": None # Default formatter works well with array data
        },
        "legend": {
            "data": ["Weight (%)", "Deriv. Weight (%/K)"],
            "top": "5%"
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (K)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": "dataMin",
            "max": "dataMax",
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
                "name": "Deriv. Weight (%/K)",
                "position": "right",
                "min": -3, # Adjust based on data range, min was ~-2.4
                "max": 1,  # Max was ~0.002, so 1 is safe
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#5470c6"
                },
                "itemStyle": {
                    "color": "#5470c6"
                },
                "data": weight_data,
                "yAxisIndex": 0
            },
            {
                "name": "Deriv. Weight (%/K)",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#91cc75"
                },
                "itemStyle": {
                    "color": "#91cc75"
                },
                "data": deriv_data,
                "yAxisIndex": 1
            }
        ]
    }
    
    result = {
        "figures": [
            {
                "name": "plot1",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
