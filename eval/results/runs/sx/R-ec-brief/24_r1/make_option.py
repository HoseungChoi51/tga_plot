import pandas as pd
import numpy as np
import json

def generate_plot():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
    
    # Read the Excel file
    df = pd.read_excel(file_path, sheet_name="CNT-01")
    
    # Extract data columns based on preview info
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    heat_flow_col = "Heat Flow (W/g)"
    
    # Prepare data for ECharts
    x_data = df[temp_col].dropna().tolist()
    y1_data = df[weight_col].dropna().tolist()
    y2_data = df[heat_flow_col].dropna().tolist()
    
    # Ensure lengths match by taking min length of valid rows if necessary, 
    # but usually TGA data is aligned. We'll zip them carefully.
    # Filter out rows where any of the required columns are NaN
    mask = df[[temp_col, weight_col, heat_flow_col]].notna().all(axis=1)
    clean_df = df[mask]
    
    x_vals = clean_df[temp_col].values
    y1_vals = clean_df[weight_col].values
    y2_vals = clean_df[heat_flow_col].values
    
    series_weight = [[float(x), float(y)] for x, y in zip(x_vals, y1_vals)]
    series_heat = [[float(x), float(y)] for x, y in zip(x_vals, y2_vals)]
    
    # Calculate Residue at 800°C for label
    residue_label = ""
    residue_point = None
    if len(x_vals) > 0:
        idx_800 = np.argmin(np.abs(x_vals - 800))
        residue_val = y1_vals[idx_800]
        residue_temp = x_vals[idx_800]
        residue_label = f"Residue {residue_val:.1f}%"
        residue_point = [float(residue_temp), float(residue_val)]

    # Build ECharts Option
    option = {
        "title": {
            "text": "CNT-01",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": ["Weight (%)", "Heat flow (W/g)"],
            "top": "5%",
            "right": "5%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
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
            "axisLabel": {
                "formatter": "{value}"
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#1f4e9c"
                    }
                },
                "axisLabel": {
                    "formatter": "{value}",
                    "color": "#1f4e9c"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed"
                    }
                }
            },
            {
                "type": "value",
                "name": "Heat flow (W/g)",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#c0392b"
                    }
                },
                "axisLabel": {
                    "formatter": "{value}",
                    "color": "#c0392b"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": series_weight,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": residue_point,
                            "value": residue_label,
                            "symbolSize": 10,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            },
                            "label": {
                                "show": True,
                                "formatter": residue_label,
                                "position": "top",
                                "color": "#1f4e9c",
                                "fontSize": 10
                            }
                        }
                    ]
                }
            },
            {
                "name": "Heat flow (W/g)",
                "type": "line",
                "yAxisIndex": 1,
                "data": series_heat,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                }
            }
        ]
    }
    
    figure = {
        "name": "plot1",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }
    
    output = {"figures": [figure]}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    generate_plot()
