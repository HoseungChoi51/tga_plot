import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    
    figures = []
    
    for sheet_name in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
        
        # Clean column names if needed (remove spaces or special chars for consistency, though here they look fine)
        # Based on preview: Time, Temperature, Weight(%), D.W(%/C)
        
        x_col = "Temperature"
        y1_col = "Weight(%)"
        y2_col = "D.W(%/C)"
        
        # Prepare data
        temp = df[x_col].tolist()
        weight = df[y1_col].tolist()
        d_weight = df[y2_col].tolist()
        
        # Create series data for ECharts
        # Series 1: Weight (%) - Left Y axis
        series_weight = {
            "name": f"{sheet_name} - Weight",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temp, weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "itemStyle": {"color": "#5470c6"} # Default blue-ish
        }
        
        # Series 2: D.W (%/C) - Right Y axis
        series_dw = {
            "name": f"{sheet_name} - D.W",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[t, dw] for t, dw in zip(temp, d_weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "type": "dashed"},
            "itemStyle": {"color": "#ee6666"} # Default red-ish
        }
        
        # MarkLine for 450 C
        mark_line_data = [
            {
                "xAxis": 450,
                "label": {
                    "show": True,
                    "formatter": "산화 시작",
                    "position": "insideEndTop",
                    "fontSize": 12,
                    "color": "#333"
                },
                "lineStyle": {
                    "color": "#999",
                    "type": "solid",
                    "width": 1.5
                }
            }
        ]
        
        # Attach markLine to the first series (or both, but usually one is enough visually if they share X axis)
        # Attaching to weight series makes it visible clearly against the left axis context
        series_weight["markLine"] = {
            "silent": True,
            "symbol": ["none", "none"],
            "data": mark_line_data
        }

        option = {
            "title": {
                "text": f"TGA Data: {sheet_name}",
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
                "data": [series_weight["name"], series_dw["name"]],
                "top": 30
            },
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "containLabel": True
            },
            "toolbox": {
                "feature": {
                    "saveAsImage": {}
                }
            },
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 30,
                "min": 30,
                "max": 900 if "normal" in sheet_name or "acid" in sheet_name else 750,
                "axisLabel": {
                    "formatter": "{value}"
                }
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "position": "left",
                    "min": 0,
                    "max": 105
                },
                {
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "position": "right",
                    "offset": 0
                }
            ],
            "series": [series_weight, series_dw]
        }
        
        fig_entry = {
            "name": f"tga_{sheet_name.replace(' ', '_')}",
            "option": option,
            "width": 800,
            "height": 500,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(fig_entry)

    output = {"figures": figures}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
