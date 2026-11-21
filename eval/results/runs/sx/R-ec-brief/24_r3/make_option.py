import pandas as pd
import numpy as np
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
    
    # Read the Excel file
    df = pd.read_excel(file_path, sheet_name='CNT-01')
    
    # Extract columns based on the preview and request
    # x: Temperature (°C) -> Column B
    # y1: Weight (%) -> Column E
    # y2: Heat Flow (W/g) -> Column F
    
    temp = df['Temperature (°C)'].values
    weight_pct = df['Weight (%)'].values
    heat_flow = df['Heat Flow (W/g)'].values
    
    # Filter out NaN values if any
    mask = ~np.isnan(temp) & ~np.isnan(weight_pct) & ~np.isnan(heat_flow)
    temp = temp[mask]
    weight_pct = weight_pct[mask]
    heat_flow = heat_flow[mask]
    
    # Calculate Residue at nearest 800 °C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight_pct[idx_800]
    residue_temp = temp[idx_800]
    
    # Prepare data for ECharts
    # Data format for line series: [[x, y], ...]
    data_y1 = [[float(t), float(w)] for t, w in zip(temp, weight_pct)]
    data_y2 = [[float(t), float(h)] for t, h in zip(temp, heat_flow)]
    
    # Build the ECharts option
    option = {
        "title": {
            "text": "CNT-01",
            "left": "center",
            "top": 10,
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
            "data": ["Weight (%)", "Heat Flow (W/g)"],
            "left": "left",
            "top": "middle",
            "orient": "vertical",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "15%",
            "right": "15%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
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
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
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
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
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
                "data": data_y1,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "symbol": "none",
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(residue_temp), float(residue_val)],
                            "value": f"Residue {residue_val:.1f}%",
                            "symbolSize": 8,
                            "label": {
                                "show": True,
                                "formatter": "{b}",
                                "position": "right",
                                "distance": 5,
                                "fontFamily": "Noto Sans CJK KR",
                                "color": "#1f4e9c"
                            },
                            "itemStyle": {
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                }
            },
            {
                "name": "Heat Flow (W/g)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data_y2,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#c0392b"
                },
                "symbol": "none"
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
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
