import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def get_tga_plot_option(df, sheet_name):
    # Identify columns based on standard TGA structure or the provided guess
    # Assuming: B=Temperature, C=Weight(%), D=D.W(%/C)
    # We will look for these specific names if possible, otherwise use indices
    
    cols = df.columns.tolist()
    
    # Try to find temperature column
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in cl and 'd.w' not in cl and 'derivative' not in cl:
            weight_col = c
        elif 'd.w' in cl or 'derivative' in cl or 'dtg' in cl:
            dtg_col = c
            
    # Fallback to indices if names aren't clear (based on preview: A=Time, B=Temp, C=Weight, D=DTG)
    if temp_col is None: temp_col = cols[1]
    if weight_col is None: weight_col = cols[2]
    if dtg_col is None: dtg_col = cols[3]

    x_data = df[temp_col].dropna().values
    y1_data = df[weight_col].dropna().values
    y2_raw = df[dtg_col].dropna().values
    
    # Align lengths just in case of NaN drops differing
    min_len = min(len(x_data), len(y1_data), len(y2_raw))
    x_data = x_data[:min_len]
    y1_data = y1_data[:min_len]
    y2_raw = y2_raw[:min_len]
    
    # DTG is multiplied by -1 so peaks point up
    y2_data = [-v for v in y2_raw]

    # Calculate Residue at ~800°C
    residue_val = 0.0
    residue_temp = 800.0
    if len(x_data) > 0:
        idx_800 = np.argmin(np.abs(x_data - 800))
        residue_val = y1_data[idx_800]
        residue_temp = x_data[idx_800]
        
    # Find highest DTG peak above 150°C
    peak_temp = 0.0
    max_dtg_val = -np.inf
    found_peak = False
    for i, t in enumerate(x_data):
        if t > 150:
            val = y2_data[i] # Already negated, so looking for max positive value
            if val > max_dtg_val:
                max_dtg_val = val
                peak_temp = t
                found_peak = True
                
    if not found_peak:
        peak_temp = 0.0
        
    # Axis ranges
    x_min = float(min(x_data))
    x_max = float(max(x_data))
    y1_min = float(min(y1_data))
    y1_max = float(max(y1_data))
    y2_min = float(min(y2_data))
    y2_max = float(max(y2_data))
    
    # Add some padding to axes
    x_pad = (x_max - x_min) * 0.05
    y1_pad = (y1_max - y1_min) * 0.05
    y2_pad = (y2_max - y2_min) * 0.05 if (y2_max - y2_min) > 0 else 1.0
    
    # Markers data
    markers = []
    # Residue marker
    markers.append({
        "coord": [residue_temp, residue_val],
        "symbol": "circle",
        "symbolSize": 6,
        "itemStyle": {"color": "#1f4e9c"}
    })
    # Peak marker
    if found_peak:
        # The peak marker should be on the DTG curve (y2 axis)
        # But scatter series usually map to one yAxisIndex. 
        # We can add a separate scatter series for the peak marker on y2
        pass

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "2%",
            "textStyle": {
                "fontSize": 14,
                "fontWeight": "bold",
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
            "data": ["무게 (%)", "미분 무게 (%/°C)"],
            "left": "center",
            "top": "10%",
            "orient": "horizontal",
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
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": round(x_min - x_pad, 1),
            "max": round(x_max + x_pad, 1),
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            }
        },
        "yAxis": [
            {
                "name": "무게 (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "left",
                "min": round(y1_min - y1_pad, 1),
                "max": round(y1_max + y1_pad, 1),
                "axisLabel": {
                    "formatter": "{value}",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#ccc"
                    }
                }
            },
            {
                "name": "미분 무게 (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "min": round(y2_min - y2_pad, 1),
                "max": round(y2_max + y2_pad, 1),
                "axisLabel": {
                    "formatter": "{value}",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": "무게 (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": [[float(t), float(w)] for t, w in zip(x_data, y1_data)],
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(residue_temp), float(residue_val)],
                            "value": f"Residue {residue_val:.1f}%",
                            "symbol": "circle",
                            "symbolSize": 8,
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": "{@[0]} °C\n{@[1]:.1f}%",
                                "backgroundColor": "rgba(255,255,255,0.8)",
                                "padding": [2, 4],
                                "borderRadius": 2,
                                "fontFamily": "Noto Sans CJK KR"
                            },
                            "itemStyle": {
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                }
            },
            {
                "name": "미분 무게 (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": [[float(t), float(d)] for t, d in zip(x_data, y2_data)],
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(peak_temp), float(max_dtg_val)],
                            "value": f"{peak_temp:.0f} °C",
                            "symbol": "triangle",
                            "symbolSize": 8,
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": "{@[0]:.0f} °C",
                                "backgroundColor": "rgba(255,255,255,0.8)",
                                "padding": [2, 4],
                                "borderRadius": 2,
                                "fontFamily": "Noto Sans CJK KR"
                            },
                            "itemStyle": {
                                "color": "#c0392b"
                            }
                        }
                    ] if found_peak else []
                }
            }
        ]
    }
    
    return option

figures = []

try:
    xl = pd.ExcelFile(DATA_FILE)
    sheet_names = xl.sheet_names
    
    for s_name in sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=s_name)
        opt = get_tga_plot_option(df, s_name)
        
        figures.append({
            "name": s_name.replace(" ", "_").replace("/", "_"),
            "option": opt,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })
except Exception as e:
    # If error, return empty figures list or handle gracefully
    pass

output = {
    "figures": figures
}

print(json.dumps(output, ensure_ascii=False))
