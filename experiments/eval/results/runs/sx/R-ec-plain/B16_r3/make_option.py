import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
    
    # Read the CSV file
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return

    # Extract columns based on the preview
    # Time (min), Temperature (°C), Weight (%), Deriv. Weight (%/°C), Heat Flow (W/g)
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    dtg_col = "Deriv. Weight (%/°C)"
    
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        print(json.dumps({"error": "Required columns not found"}))
        return

    # Prepare data for ECharts
    # Convert to lists of [x, y] pairs
    tga_data = [[float(t), float(w)] for t, w in zip(df[temp_col], df[weight_col])]
    dtg_data = [[float(t), float(d)] for t, d in zip(df[temp_col], df[dtg_col])]
    
    # Define common X-axis configuration
    x_axis_config = {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "formatter": "{value}"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed"
            }
        }
    }

    # Figure 1: TGA (Weight %) - Top
    option_tga = {
        "title": {
            "text": "TGA Curve",
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "grid": {
            "left": "10%",
            "right": "5%",
            "top": "15%",
            "bottom": "20%"
        },
        "xAxis": x_axis_config,
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "inverse": False, # Usually TGA starts high and goes low, but standard axis is fine unless specified otherwise. 
                             # Standard scientific plots often keep Y increasing upwards. 
                             # Let's keep it standard (increasing up).
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "data": tga_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#007ACC"
                },
                "areaStyle": {
                    "opacity": 0.1
                }
            }
        ]
    }

    # Figure 2: DTG (Deriv. Weight %/°C) - Bottom
    option_dtg = {
        "title": {
            "text": "DTG Curve",
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "grid": {
            "left": "10%",
            "right": "5%",
            "top": "15%",
            "bottom": "20%"
        },
        "xAxis": x_axis_config,
        "yAxis": {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": [
            {
                "name": "DTG",
                "type": "line",
                "data": dtg_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#D62728"
                }
            }
        ]
    }

    figures = [
        {
            "name": "tga_weight",
            "option": option_tga,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        },
        {
            "name": "dtg_derivative",
            "option": option_dtg,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]

    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
