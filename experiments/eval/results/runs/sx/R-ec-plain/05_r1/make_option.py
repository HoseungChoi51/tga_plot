import pandas as pd
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def main():
    # Read all sheets from the Excel file
    xl = pd.ExcelFile(DATA_FILE)
    sheet_names = xl.sheet_names
    
    series_list = []
    
    # Define colors for different samples (y1 - Weight %)
    y1_colors = ['#000000', '#FF0000', '#0000FF']  # Black, Red, Blue
    
    # Define colors for different samples (y2 - DTG %)
    y2_colors = ['#666666', '#CC0000', '#0000CC']  # Dark Gray, Dark Red, Dark Blue
    
    for idx, sheet_name in enumerate(xl.sheet_names):
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        
        # Extract columns based on preview info
        # Assuming column names are consistent: Temperature, Weight(%), D.W(%/C)
        temp_col = 'Temperature'
        weight_col = 'Weight(%)'
        dtg_col = 'D.W(%/C)'
        
        if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
            continue
            
        temps = df[temp_col].dropna().tolist()
        weights = df[weight_col].dropna().tolist()
        dtgs = df[dtg_col].dropna().tolist()
        
        # Prepare data points [x, y]
        tga_data = [[t, w] for t, w in zip(temps, weights)]
        dtg_data = [[t, d] for t, d in zip(temps, dtgs)]
        
        # Y1 Series: Weight (%)
        color_y1 = y1_colors[idx % len(y1_colors)]
        series_list.append({
            "name": f"{sheet_name} TGA",
            "type": "line",
            "yAxisIndex": 0,
            "data": tga_data,
            "showSymbol": False,
            "lineStyle": {
                "color": "#000000" if idx == 0 else color_y1, # Request says y1 line color black. If multiple, maybe first is black? 
                # Re-reading request: "y1 선 색깔 검정". It implies ALL y1 lines should be black? Or just one? 
                # Usually in multi-sample plots, distinct colors are preferred unless specified otherwise.
                # However, the prompt specifically says "y1 선 색깔 검정" (Y1 line color black).
                # If there are multiple sheets, making them all black might be confusing. 
                # But let's follow the instruction strictly for the visual property requested.
                # Actually, looking at typical requests, if they specify a specific style like "black", it often applies to the primary curve or they want consistency.
                # Let's assume the user wants the Weight curves to be black.
                # Wait, if I make all 3 black, they overlap. 
                # Let's look at the phrasing again: "y1 선 색깔 검정, 선 굵기 2.5로 하고 y2 선은 점선으로 해줘"
                # It doesn't say "all". But usually, if you have multiple datasets, you distinguish them.
                # Perhaps the user considers "Weight" as the single category of interest to be styled uniformly?
                # Or maybe they only care about the styling properties defined.
                # Let's set Y1 lines to Black as requested. To distinguish, we could use different dash patterns or symbols, but the request didn't ask for that.
                # A safer interpretation for a lab report where comparison is key: Maybe the user made a mistake and meant "make the axes black" or similar? No, "y1 선" means Y1 series line.
                # I will apply the style to all Y1 series as requested. If visibility is an issue, the user can adjust later.
                # However, standard practice suggests distinct colors. Let's stick to the explicit instruction: Color Black.
                "color": "#000000",
                "width": 2.5
            },
            "emphasis": {
                "focus": "series"
            }
        })
        
        # Y2 Series: DTG (%)
        # Request: "y2 선은 점선으로 해줘" (Make Y2 lines dashed)
        color_y2 = y2_colors[idx % len(y2_colors)]
        series_list.append({
            "name": f"{sheet_name} DTG",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "lineStyle": {
                "color": color_y2, # Keep distinct colors for DTG to help readability if needed, or match Y1? 
                # The request didn't specify color for Y2, only dash style.
                # Using distinct colors helps separate the two metrics visually.
                "type": "dashed",
                "width": 1.5
            },
            "emphasis": {
                "focus": "series"
            }
        })

    option = {
        "backgroundColor": "#FFFFFF",
        "title": {
            "text": "TGA / DTG Analysis",
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
            },
            "formatter": None # Default formatter works well with array data
        },
        "legend": {
            "data": [s["name"] for s in series_list],
            "top": 40,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 0,
            "max": 900,
            "axisLine": {
                "lineStyle": {
                    "color": "#333333"
                }
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "color": "#EEEEEE"
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
                "max": 100,
                "axisLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#333333"
                    }
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#EEEEEE"
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
                "min": -1.2,
                "max": 0.1,
                "axisLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#333333"
                    }
                },
                "splitLine": {
                    "show": False
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            }
        ],
        "series": series_list
    }

    output = {
        "figures": [
            {
                "name": "plot1",
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
