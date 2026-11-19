import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets from the Excel file
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    
    figures = []
    
    # Define common style settings based on user request: gray text, size 13
    common_text_style = {
        "color": "#808080",
        "fontSize": 13,
        "fontFamily": "Noto Sans CJK KR"
    }
    
    # Prepare series data for each sheet
    series_list = []
    legend_data = []
    
    colors = ["#5470c6", "#91cc75", "#fac858"] # Distinct colors for lines
    
    for i, name in enumerate(sheet_names):
        df = pd.read_excel(file_path, sheet_name=name)
        
        # Extract columns based on preview info
        x_col = "Temperature"
        y1_col = "Weight(%)"
        y2_col = "D.W(%/C)"
        
        # Clean data: remove NaN if any
        df_clean = df[[x_col, y1_col, y2_col]].dropna()
        
        temp_vals = df_clean[x_col].tolist()
        weight_vals = df_clean[y1_col].tolist()
        dw_vals = df_clean[y2_col].tolist()
        
        # Create TGA curve (Weight %)
        series_list.append({
            "name": f"{name} - Weight(%)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temp_vals, weight_vals)],
            "lineStyle": {"width": 2, "color": colors[i % len(colors)]},
            "itemStyle": {"color": colors[i % len(colors)]}
        })
        
        # Create DTG curve (D.W %/C)
        series_list.append({
            "name": f"{name} - D.W(%/C)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(temp_vals, dw_vals)],
            "lineStyle": {"width": 1.5, "color": colors[i % len(colors)], "type": "dashed"},
            "itemStyle": {"color": colors[i % len(colors)]}
        })
        
        legend_data.append(f"{name} - Weight(%)")
        legend_data.append(f"{name} - D.W(%/C)")

    option = {
        "backgroundColor": "transparent",
        "title": {
            "text": "TGA Analysis Results",
            "left": "center",
            "textStyle": common_text_style
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "textStyle": common_text_style
        },
        "legend": {
            "data": legend_data,
            "bottom": 0,
            "textStyle": common_text_style,
            "icon": "rect",
            "itemWidth": 15,
            "itemHeight": 10
        },
        "grid": {
            "top": 60,
            "left": 60,
            "right": 60,
            "bottom": 80,
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": common_text_style,
            "axisLabel": {
                **common_text_style
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#808080"
                }
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "color": "#e0e0e0"
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "nameTextStyle": common_text_style,
                "axisLabel": {
                    **common_text_style
                },
                "axisLine": {
                    "lineStyle": {
                        "color": "#808080"
                    }
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#e0e0e0"
                    }
                }
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "position": "right",
                "nameTextStyle": common_text_style,
                "axisLabel": {
                    **common_text_style
                },
                "axisLine": {
                    "lineStyle": {
                        "color": "#808080"
                    }
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": series_list
    }

    result = {
        "figures": [
            {
                "name": "tga_analysis",
                "option": option,
                "width": 800,
                "height": 600,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
