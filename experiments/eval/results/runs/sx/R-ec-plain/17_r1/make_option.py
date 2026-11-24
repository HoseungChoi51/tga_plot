import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Sheet names to plot
    sheets = [
        "1006R1-V normal",
        "1006R1-V acid",
        "1006R1-V 750C"
    ]
    
    figures = []
    
    for sheet_name in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Extract data columns based on the preview info
        x_data = df['Temperature'].tolist()
        y1_data = df['Weight(%)'].tolist()
        y2_data = df['D.W(%/C)'].tolist()
        
        # Create ECharts option
        option = {
            "title": {
                "text": f"TGA Analysis - {sheet_name}",
                "left": "center",
                "top": 10,
                "textStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 14
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                },
                "formatter": None  # Using default formatter since JS functions are not allowed
            },
            "legend": {
                "data": ["Weight (%)", "DTG (%/°C)"],
                "top": 30,
                "textStyle": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True
            },
            "xAxis": {
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 25,
                "type": "value",
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            "yAxis": [
                {
                    "name": "Weight (%)",
                    "type": "value",
                    "position": "left",
                    "nameTextStyle": {
                        "fontFamily": "Noto Sans CJK KR"
                    },
                    "axisLabel": {
                        "fontFamily": "Noto Sans CJK KR"
                    }
                },
                {
                    "name": "DTG (%/°C)",
                    "type": "value",
                    "position": "right",
                    "nameTextStyle": {
                        "fontFamily": "Noto Sans CJK KR"
                    },
                    "axisLabel": {
                        "fontFamily": "Noto Sans CJK KR"
                    }
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "smooth": True,
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "data": [[x, y] for x, y in zip(x_data, y1_data)],
                    "itemStyle": {
                        "color": "#5470c6"
                    },
                    "lineStyle": {
                        "width": 2
                    }
                },
                {
                    "name": "DTG (%/°C)",
                    "type": "line",
                    "smooth": True,
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "data": [[x, y] for x, y in zip(x_data, y2_data)],
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
            "name": sheet_name.replace(" ", "_"),
            "option": option,
            "width": 8 * 96,  # 8 inches at 96 dpi -> 768 px
            "height": 5 * 96, # 5 inches at 96 dpi -> 480 px
            "dpi": 600,
            "formats": ["png"]
        }
        figures.append(figure)
        
    result = {"figures": figures}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
