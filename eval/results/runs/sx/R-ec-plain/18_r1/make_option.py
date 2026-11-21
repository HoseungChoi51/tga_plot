import pandas as pd
import numpy as np
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    
    figures = []
    
    for sheet_name in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Identify columns based on the preview structure
        # Time, Temperature, Weight(%), D.W(%/C)
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dtg_col = 'D.W(%/C)'
        
        if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
            continue
            
        x_data = df[temp_col].dropna().tolist()
        y1_data = df[weight_col].dropna().tolist()
        y2_data = df[dtg_col].dropna().tolist()
        
        # Ensure lengths match after dropna (though they should be aligned rows)
        min_len = min(len(x_data), len(y1_data), len(y2_data))
        x_data = x_data[:min_len]
        y1_data = y1_data[:min_len]
        y2_data = y2_data[:min_len]
        
        series = [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": [[x, y] for x, y in zip(x_data, y1_data)],
                "yAxisIndex": 0,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {"width": 2}
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": [[x, y] for x, y in zip(x_data, y2_data)],
                "yAxisIndex": 1,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {"width": 2, "type": "dashed"}
            }
        ]
        
        option = {
            "title": {
                "text": f"TGA Analysis: {sheet_name}",
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
                "data": ["Weight (%)", "DTG (%/°C)"],
                "top": "8%"
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
                "minInterval": 100,
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
                    "max": 110
                },
                {
                    "type": "value",
                    "name": "DTG (%/°C)",
                    "position": "right",
                    "min": -1.2,
                    "max": 0.05
                }
            ],
            "series": series
        }
        
        fig_entry = {
            "name": f"tga_{sheet_name.replace(' ', '_')}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(fig_entry)
        
    result = {"figures": figures}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
