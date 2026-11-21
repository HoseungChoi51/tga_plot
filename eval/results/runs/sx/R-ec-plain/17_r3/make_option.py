import pandas as pd
import numpy as np
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets
    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names
    
    figures = []
    
    # We will create two plots: one for TGA (Weight %) and one for DTG (D.W %/C)
    # Or combine them? The request asks for "그림" (picture/chart). 
    # Usually TGA data is presented with Weight on left Y-axis and DTG on right Y-axis, or separate plots.
    # Given the request doesn't specify separation, a combined plot with dual Y-axes is standard for TGA/DTG.
    # However, having 3 samples on one chart might be cluttered. Let's make one comprehensive chart.
    
    # Data preparation
    tga_series = []
    dtg_series = []
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Blue, Orange, Green
    
    for i, name in enumerate(sheet_names):
        df = pd.read_excel(file_path, sheet_name=name)
        
        # Extract columns based on preview info
        temp = df['Temperature'].values
        weight = df['Weight(%)'].values
        dw = df['D.W(%/C)'].values
        
        # Clean NaN if any just in case
        mask = ~np.isnan(temp) & ~np.isnan(weight) & ~np.isnan(dw)
        temp = temp[mask]
        weight = weight[mask]
        dw = dw[mask]
        
        # Create pairs for ECharts [x, y]
        tga_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
        dtg_data = [[float(t), float(d)] for t, d in zip(temp, dw)]
        
        color = colors[i % len(colors)]
        
        # TGA Series (Left Y Axis)
        tga_series.append({
            "name": f"{name} (TGA)",
            "type": "line",
            "data": tga_data,
            "showSymbol": False,
            "smooth": True,
            "yAxisIndex": 0,
            "itemStyle": {"color": color},
            "lineStyle": {"width": 2}
        })
        
        # DTG Series (Right Y Axis)
        dtg_series.append({
            "name": f"{name} (DTG)",
            "type": "line",
            "data": dtg_data,
            "showSymbol": False,
            "smooth": True,
            "yAxisIndex": 1,
            "itemStyle": {"color": color},
            "lineStyle": {"width": 1.5, "type": "dashed"}
        })

    # Combine series
    all_series = tga_series + dtg_series
    
    # Option definition
    option = {
        "backgroundColor": "#ffffff",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": "{a0}: <br/> Temp: {b0}<br/> Weight: {c0}%<br/> DTG: {c1}%/C" # Simplified formatter
        },
        "legend": {
            "data": [s["name"] for s in all_series],
            "top": "5%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            }
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "12%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 0,
            "max": 900,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#eee"
                }
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 105,
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee"
                    }
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "position": "right",
                "min": -1.1,
                "max": 0.1,
                "splitLine": {
                    "show": False
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            }
        ],
        "series": all_series
    }
    
    # Dimensions: Width 8 inches, Height 5 inches at 600 DPI
    # CSS pixels at 96 px/inch -> Width = 8 * 96 = 768, Height = 5 * 96 = 480
    width_px = int(8 * 96)
    height_px = int(5 * 96)
    dpi = 600
    
    figure_entry = {
        "name": "tga_dtg_combined",
        "option": option,
        "width": width_px,
        "height": height_px,
        "dpi": dpi,
        "formats": ["png"]
    }
    
    output = {
        "figures": [figure_entry]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
