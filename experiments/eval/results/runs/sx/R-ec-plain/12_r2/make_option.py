import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    
    series_list = []
    
    # Define colors for different samples
    colors = ['#5470c6', '#91cc75', '#fac858']
    
    for i, name in enumerate(sheet_names):
        df = pd.read_excel(xls, sheet_name=name)
        
        # Clean column names if necessary (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identify columns based on the preview structure
        # X: Temperature, Y1: Weight(%), Y2: D.W(%/C)
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dw_col = 'D.W(%/C)'
        
        # Extract data
        x_data = df[temp_col].tolist()
        y_weight = df[weight_col].tolist()
        y_dw = df[dw_col].tolist()
        
        # Create TGA series (Weight %) - Primary Y axis
        tga_series = {
            "name": f"{name} (TGA)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "data": [[x, y] for x, y in zip(x_data, y_weight)],
            "yAxisIndex": 0,
            "itemStyle": {"color": colors[i % len(colors)]},
            "lineStyle": {"width": 2}
        }
        
        # Create DTG series (D.W %/C) - Secondary Y axis
        dtg_series = {
            "name": f"{name} (DTG)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "data": [[x, y] for x, y in zip(x_data, y_dw)],
            "yAxisIndex": 1,
            "itemStyle": {"color": colors[i % len(colors)]},
            "lineStyle": {"width": 1.5, "type": "dashed"},
            "opacity": 0.7
        }
        
        series_list.append(tga_series)
        series_list.append(dtg_series)

    # Prepare the ECharts option
    option = {
        "title": {
            "text": "TGA/DTG Analysis Comparison",
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
            },
            "formatter": None # Default formatter works well with array data
        },
        "legend": {
            "data": [f"{n} (TGA)" for n in sheet_names] + [f"{n} (DTG)" for n in sheet_names],
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
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 30,
            "max": 900,
            "axisLine": {"onZero": False},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": "#5470c6"}},
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "Rate of Weight Loss (%/°C)",
                "position": "right",
                "min": -1.1,
                "max": 0.1,
                "axisLine": {"show": True, "lineStyle": {"color": "#91cc75"}},
                "splitLine": {"show": False}
            }
        ],
        "series": series_list,
        "graphic": [
            {
                "type": "line",
                "shape": {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 1000 # Will be clipped by grid
                },
                "style": {
                    "stroke": "#ff0000",
                    "lineWidth": 2,
                    "lineDash": [5, 5]
                },
                "z": 100,
                # We need to position this relative to the xAxis value 450.
                # In ECharts graphic component, positioning is tricky without JS functions.
                # Alternative: Use markLine on one of the series or use a custom series.
                # However, the simplest way to add a vertical line at a specific x-value 
                # that spans the entire plot area is using markLine on any series.
            }
        ]
    }
    
    # Remove the incomplete graphic object and use markLine instead which is more robust for static JSON generation
    del option["graphic"]
    
    # Add markLine to the first TGA series (or all, but usually one is enough visually if they overlap)
    # Adding to the first series ensures it appears.
    if series_list:
        series_list[0]["markLine"] = {
            "silent": True,
            "symbol": ["none", "none"],
            "label": {
                "show": True,
                "position": "end",
                "formatter": "산화 시작",
                "distance": [0, -10],
                "color": "#ff0000",
                "fontSize": 12,
                "fontWeight": "bold",
                "backgroundColor": "rgba(255, 255, 255, 0.8)",
                "padding": [2, 4],
                "borderRadius": 2
            },
            "lineStyle": {
                "color": "#ff0000",
                "type": "dashed",
                "width": 2
            },
            "data": [
                {
                    "xAxis": 450
                }
            ]
        }

    output = {
        "figures": [
            {
                "name": "tga_comparison",
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
