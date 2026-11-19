import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
    
    # Read the Excel file
    df = pd.read_excel(file_path, sheet_name="CNT-01")
    
    # Extract necessary columns based on the preview
    # Temperature (°C) is column B -> index 1 in DataFrame (0-based after header)
    # Weight (%) is column E -> index 4
    # Heat Flow (W/g) is column F -> index 5
    
    temp = df['Temperature (°C)'].dropna().tolist()
    weight = df['Weight (%)'].dropna().tolist()
    heat_flow = df['Heat Flow (W/g)'].dropna().tolist()
    
    # Ensure lengths match by taking the minimum length or filtering common indices if needed.
    # Assuming rows are aligned:
    min_len = min(len(temp), len(weight), len(heat_flow))
    temp = temp[:min_len]
    weight = weight[:min_len]
    heat_flow = heat_flow[:min_len]
    
    # Construct the ECharts option
    option = {
        "backgroundColor": "#ffffff",
        "title": {
            "text": "TGA & DSC Analysis",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
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
            "top": "8%",
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
        "xAxis": [
            {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 30,
                "axisLabel": {
                    "formatter": "{value} °C"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#5470c6"
                    }
                },
                "axisLabel": {
                    "formatter": "{value} %"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#eee"
                    }
                }
            },
            {
                "type": "value",
                "name": "Heat flow (W/g)",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#ee6666"
                    }
                },
                "axisLabel": {
                    "formatter": "{value}"
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
                "smooth": True,
                "showSymbol": False,
                "data": [[t, w] for t, w in zip(temp, weight)],
                "yAxisIndex": 0,
                "itemStyle": {
                    "color": "#5470c6"
                },
                "lineStyle": {
                    "width": 2
                }
            },
            {
                "name": "Heat Flow (W/g)",
                "type": "line",
                "smooth": True,
                "showSymbol": False,
                "data": [[t, h] for t, h in zip(temp, heat_flow)],
                "yAxisIndex": 1,
                "itemStyle": {
                    "color": "#ee6666"
                },
                "lineStyle": {
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
    print(json.dumps(output))

if __name__ == "__main__":
    main()
