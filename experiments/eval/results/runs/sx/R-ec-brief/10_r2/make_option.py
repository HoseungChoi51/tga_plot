import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def make_tga_chart(df, sheet_name):
    # Identify columns based on standard TGA structure or guesses from preview
    cols = df.columns.tolist()
    
    # Heuristic to find columns if names vary slightly, but here we rely on the provided guess structure
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temp' in c_lower:
            x_col = c
        elif 'weight' in c_lower and '%' in c_lower:
            y1_col = c
        elif ('d.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower) and '%' in c_lower:
            y2_col = c
            
    # Fallback to position if heuristic fails (based on typical A=Time, B=Temp, C=Weight, D=DTG)
    if x_col is None and len(cols) > 1: x_col = cols[1]
    if y1_col is None and len(cols) > 2: y1_col = cols[2]
    if y2_col is None and len(cols) > 3: y2_col = cols[3]
    
    if not all([x_col, y1_col, y2_col]):
        return None

    data = df[[x_col, y1_col, y2_col]].dropna()
    if data.empty:
        return None
        
    temps = data[x_col].values
    weights = data[y1_col].values
    dtgs = data[y2_col].values * -1.0  # Invert DTG so peaks point up
    
    # Find Residue at 700°C with 2 decimal places
    target_temp = 700.0
    idx_residue = np.argmin(np.abs(temps - target_temp))
    residue_val = weights[idx_residue]
    residue_temp = temps[idx_residue]
    residue_label = f"Residue {residue_val:.2f}%"
    
    # Find Peak temperature (highest DTG above 150°C)
    mask = temps > 150.0
    if np.any(mask):
        filtered_dtgs = dtgs[mask]
        filtered_temps = temps[mask]
        peak_idx_local = np.argmax(filtered_dtgs)
        peak_temp = filtered_temps[peak_idx_local]
        peak_val = filtered_dtgs[peak_idx_local]
        peak_label = f"{peak_temp:.0f} °C"
        
        # Marker for peak
        peak_marker = [float(peak_temp), float(peak_val)]
    else:
        peak_label = ""
        peak_marker = []

    # Prepare series data
    # Weight Series (y1)
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # DTG Series (y2)
    dtg_data = [[float(t), float(d)] for t, d in zip(temps, dtgs)]
    
    # Markers for annotations
    residue_marker = [[float(residue_temp), float(residue_val)]]
    
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "top",
            "textStyle": {"fontSize": 14, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "DTG (%/°C)"],
            "left": "left",
            "top": "middle",
            "orient": "vertical"
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 25,
            "splitLine": {"show": False},
            "axisTick": {"alignWithLabel": True}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": 0,
                "max": 110,
                "splitLine": {"lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "position": "right",
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": weight_data,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "symbol": "none",
                "markPoint": {
                    "data": [
                        {
                            "coord": residue_marker[0],
                            "value": residue_label,
                            "label": {
                                "show": True,
                                "formatter": "{b}",
                                "position": "right",
                                "distance": 10,
                                "fontSize": 10,
                                "color": "#1f4e9c"
                            },
                            "symbolSize": 6,
                            "itemStyle": {"color": "#1f4e9c"}
                        }
                    ]
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "itemStyle": {"color": "#c0392b"},
                "symbol": "none",
                "markPoint": {
                    "data": [
                        {
                            "coord": peak_marker,
                            "value": peak_label,
                            "label": {
                                "show": True,
                                "formatter": "{b}",
                                "position": "top",
                                "distance": 10,
                                "fontSize": 10,
                                "color": "#c0392b"
                            },
                            "symbolSize": 6,
                            "itemStyle": {"color": "#c0392b"}
                        }
                    ] if peak_marker else []
                }
            }
        ]
    }
    
    return {
        "name": sheet_name.replace(" ", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }

figures = []
xl = pd.ExcelFile(DATA_FILE)
for sheet in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet)
    chart = make_tga_chart(df, sheet)
    if chart:
        figures.append(chart)

output = {"figures": figures}
print(json.dumps(output, ensure_ascii=False))
