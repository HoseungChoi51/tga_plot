import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Sheet names and labels for the plot
    sheets_info = [
        {"name": "1006R1-V normal", "label": "Normal"},
        {"name": "1006R1-V acid", "label": "Acid"},
        {"name": "1006R1-V 750C", "label": "750C"}
    ]
    
    series_list = []
    
    # Colors for TGA (Weight %) lines - distinct colors for each sample
    tga_colors = ["#5470c6", "#91cc75", "#fac858"] 
    # Color for DTG (D.W %/C) line - requested to be green
    dtg_color = "#2ca02c" 
    
    # We will create one chart per sheet or combine them? 
    # Usually, comparing samples is done on one chart. 
    # However, having 3 samples x 2 axes might be cluttered.
    # Let's create a single combined chart with all samples' Weight (%) on Y1 
    # and maybe just one representative DTG or all DTGs on Y2?
    # The request implies modifying an existing setup where y2 is likely DTG.
    # To keep it clean and readable, I will plot all three Weight(%) curves on Y1.
    # For Y2, plotting all three DTG curves might be messy. 
    # Often, users want to see the decomposition behavior of specific samples.
    # Let's assume the user wants to compare the Normal vs Acid vs 750C.
    # I will plot Weight(%) for all three on Y1.
    # And D.W(%/C) for all three on Y2.
    # Wait, if I put all 3 DTGs on Y2 in green, they will overlap indistinguishably.
    # Standard practice: Differentiate by dash style or slight hue variation if possible, 
    # but the prompt specifically asks for "y2 line color green".
    # If there are multiple y2 series, making them ALL green makes them hard to distinguish.
    # Perhaps the user has only ONE y2 series in mind? Or maybe they want the axis label green too.
    # Let's look at the data again. It's 3 different conditions.
    # If I must make y2 green, I will use different shades of green or dash patterns for the 3 DTG lines, 
    # OR I will assume the user primarily cares about the axis styling and one main comparison.
    # However, to strictly follow "y2 line color green", I will set the primary color for DTG series to green variants.
    
    # Let's try a different approach: 
    # Maybe the user is looking at a specific sheet? No, all sheets are provided.
    # I will generate one figure containing all data.
    # Y1: Weight (%) for Normal, Acid, 750C.
    # Y2: D.W (%/C) for Normal, Acid, 750C.
    
    # To distinguish Y2 lines while keeping them "green-ish" or satisfying the constraint:
    # The constraint says "y2 선 색깔 초록으로" (Make y2 line color green).
    # If I have 3 y2 lines, I can't make them all identical green without losing info.
    # I will interpret this as: The Y2 axis theme is Green. 
    # I will use distinct shades of green for the 3 DTG lines, or better yet, 
    # since the prompt is singular ("line"), maybe they expect a single aggregated view or just care about the axis.
    # Actually, looking at typical lab requests, they often compare one control vs treated.
    # Here we have 3.
    # I will plot Weight(%) for all 3 on Y1.
    # I will plot D.W(%/C) for all 3 on Y2.
    # For Y2 colors, I will use variations of green to respect the "green" request while maintaining distinction.
    # Green shades: #2ca02c, #4caf50, #8bc34a
    
    dtg_green_shades = ["#2ca02c", "#4caf50", "#8bc34a"]
    
    for i, sheet in enumerate(sheets_info):
        df = pd.read_excel(file_path, sheet_name=sheet["name"])
        
        temp = df["Temperature"].tolist()
        weight = df["Weight(%)"].tolist()
        dw = df["D.W(%/C)"].tolist()
        
        # Series 1: Weight (%) -> Y Axis 0 (Left)
        series_list.append({
            "name": f"{sheet['label']} Weight",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temp, weight)],
            "showSymbol": False,
            "lineStyle": {
                "color": tga_colors[i],
                "width": 2
            }
        })
        
        # Series 2: D.W (%/C) -> Y Axis 1 (Right)
        series_list.append({
            "name": f"{sheet['label']} DTG",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(temp, dw)],
            "showSymbol": False,
            "lineStyle": {
                "color": dtg_green_shades[i], # Using green shades for Y2
                "width": 2
            }
        })

    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "backgroundColor": "rgba(255, 255, 255, 0.9)",
            "borderColor": "#ccc",
            "textStyle": {
                "color": "#333"
            }
        },
        "legend": {
            "data": [f"{s['label']} Weight" for s in sheets_info] + [f"{s['label']} DTG" for s in sheets_info],
            "top": "5%",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#333"
                }
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
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 14,
                    "color": "#333"
                },
                "axisLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#333"
                    }
                },
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee"
                    }
                }
            },
            {
                "type": "value",
                "name": "D.W (%/C)",
                "position": "right",
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 14,
                    "color": "#2ca02c" # Requested: Y2 axis label text color green
                },
                "axisLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#2ca02c" # Matching axis line to label
                    }
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": series_list
    }

    output = {
        "figures": [
            {
                "name": "tga_comparison",
                "option": option,
                "width": 800,
                "height": 500,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
