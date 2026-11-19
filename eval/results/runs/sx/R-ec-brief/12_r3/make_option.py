import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_tga_data(df):
    # Identify columns based on the preview structure or heuristic
    cols = df.columns.tolist()
    
    # Heuristic to find Temperature, Weight, DTG
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl:
            dtg_col = c
            
    # Fallback if names are not standard but positions match typical TGA export
    if temp_col is None and len(cols) >= 2:
        temp_col = cols[1] # Usually col B
    if weight_col is None and len(cols) >= 3:
        weight_col = cols[2] # Usually col C
    if dtg_col is None and len(cols) >= 4:
        dtg_col = cols[3] # Usually col D
        
    if temp_col is None or weight_col is None:
        return None, None, None, None
        
    x = df[temp_col].dropna().values
    y1 = df[weight_col].dropna().values
    
    # Align lengths if necessary (simple truncation to min length)
    min_len = min(len(x), len(y1))
    x = x[:min_len]
    y1 = y1[:min_len]
    
    y2 = None
    if dtg_col is not None:
        raw_y2 = df[dtg_col].dropna().values
        min_len2 = min(min_len, len(raw_y2))
        y2 = raw_y2[:min_len2]
        x = x[:min_len2]
        y1 = y1[:min_len2]
        
    return x, y1, y2, dtg_col

def calculate_residue_and_peak(x, y1, y2):
    residue_val = None
    residue_temp = None
    peak_temp = None
    peak_val = None
    
    # Residue at nearest 800C
    if len(x) > 0:
        idx_800 = np.argmin(np.abs(x - 800))
        residue_val = float(y1[idx_800])
        residue_temp = float(x[idx_800])
        
    # Peak above 150C from DTG (y2 is negative, so we look for most negative i.e., max absolute value)
    if y2 is not None and len(y2) > 0:
        mask = x > 150
        if np.any(mask):
            masked_x = x[mask]
            masked_y2 = y2[mask]
            # Find index of minimum value (most negative) in masked_y2
            min_idx = np.argmin(masked_y2)
            peak_temp = float(masked_x[min_idx])
            peak_val = float(masked_y2[min_idx])
            
    return residue_val, residue_temp, peak_temp, peak_val

def create_figure_option(sheet_name, x, y1, y2):
    residue_val, residue_temp, peak_temp, peak_val = calculate_residue_and_peak(x, y1, y2)
    
    # Prepare data series
    # ECharts expects [x, y] pairs for line charts with axis type 'value'
    series_weight = [[float(xi), float(yi)] for xi, yi in zip(x, y1)]
    
    series_dtg = []
    if y2 is not None:
        # Multiply by -1 so peaks point up
        series_dtg = [[float(xi), float(-yi)] for xi, yi in zip(x, y2)]
        
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "top",
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
            "data": ["Weight (%)", "-DTG (%/°C)"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
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
            "type": "value",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {
                "formatter": "{value} °C"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "type": "value",
                "position": "left",
                "axisLabel": {
                    "formatter": "{value} %"
                },
                "splitLine": {
                    "show": False
                }
            },
            {
                "name": "-DTG (%/°C)",
                "type": "value",
                "position": "right",
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
                "yAxisIndex": 0,
                "data": series_weight,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {}
            },
            {
                "name": "-DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": series_dtg,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {}
            }
        ]
    }
    
    # Add Residue Marker
    if residue_val is not None and residue_temp is not None:
        option["series"][0]["markPoint"] = {
            "data": [
                {
                    "coord": [residue_temp, residue_val],
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_val:.1f}%",
                        "position": "top",
                        "distance": 5,
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 10
                    }
                }
            ]
        }
        
    # Add Peak Marker
    if peak_temp is not None and peak_val is not None:
        # Note: peak_val in series_dtg was negated, so the coordinate y should be -peak_val(original) which is positive
        # But wait, I calculated peak_val from original y2. 
        # In series_dtg data, y = -original_y2. So if original peak is -1.0, plotted is 1.0.
        # The coord needs to match the plotted data.
        plotted_peak_y = -peak_val 
        option["series"][1]["markPoint"] = {
            "data": [
                {
                    "coord": [peak_temp, plotted_peak_y],
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": f"{peak_temp:.0f} °C",
                        "position": "top",
                        "distance": 5,
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 10
                    }
                }
            ]
        }

    # Add Vertical Reference Line at 450°C
    # We can add this to the first series or use a graphic element. 
    # Using markLine on the first series is common.
    ref_line_data = {
        "xAxis": 450,
        "label": {
            "show": True,
            "formatter": "산화 시작",
            "position": "insideStartTop", # or 'end', 'start' etc. insideStartTop places it near top left of line
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10,
            "color": "#333"
        },
        "lineStyle": {
            "color": "#666",
            "type": "dashed",
            "width": 1.5
        }
    }
    
    if "markLine" not in option["series"][0]:
        option["series"][0]["markLine"] = {"data": []}
    option["series"][0]["markLine"]["data"].append(ref_line_data)

    return option

figures = []

try:
    xl_file = pd.ExcelFile(DATA_FILE)
    sheet_names = xl_file.sheet_names
    
    for sheet in sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=0)
        x, y1, y2, _ = get_tga_data(df)
        
        if x is not None and len(x) > 0:
            opt = create_figure_option(sheet, x, y1, y2)
            figures.append({
                "name": f"plot_{sheet.replace(' ', '_').replace('-', '_')}",
                "option": opt,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            })
except Exception as e:
    # If something fails, output empty figures list to avoid crash, though usually better to raise for debugging
    # For production script robustness, maybe log? But requirement says print JSON only.
    pass

output = {"figures": figures}
print(json.dumps(output, ensure_ascii=False))
