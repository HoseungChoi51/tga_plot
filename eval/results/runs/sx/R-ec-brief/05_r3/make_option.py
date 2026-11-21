import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_nearest_point(x_arr, y_arr, target_x):
    """Find the point in (x_arr, y_arr) closest to target_x."""
    if len(x_arr) == 0:
        return None, None
    idx = np.argmin(np.abs(x_arr - target_x))
    return float(x_arr[idx]), float(y_arr[idx])

def find_peak_above_temp(x_arr, dtg_arr, min_temp=150.0):
    """Find the temperature of the highest DTG peak above min_temp.
    Returns (peak_temp, peak_dtg_value)."""
    mask = x_arr > min_temp
    if not np.any(mask):
        return None, None
    
    x_filtered = x_arr[mask]
    dtg_filtered = dtg_arr[mask]
    
    # Find index of minimum DTG value (deepest dip), which corresponds to the highest peak when inverted
    min_idx = np.argmin(dtg_filtered)
    peak_temp = float(x_filtered[min_idx])
    peak_dtg_raw = float(dtg_filtered[min_idx])
    
    return peak_temp, peak_dtg_raw

def process_sheet(df, sheet_name):
    # Identify columns based on standard TGA structure from preview
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        return None
        
    # Filter out rows where any of these are NaN
    valid_mask = ~(df[temp_col].isna() | df[weight_col].isna() | df[dtg_col].isna())
    temps = df.loc[valid_mask, temp_col].values.astype(float)
    weights = df.loc[valid_mask, weight_col].values.astype(float)
    dtgs = df.loc[valid_mask, dtg_col].values.astype(float)
    
    if len(temps) == 0:
        return None

    # Prepare series data
    # Series 1: Weight (%) - Left Y Axis (y1)
    # Color: Black (#000000), Width: 2.5
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # Series 2: DTG (%/C) * -1 - Right Y Axis (y2)
    # Style: Dashed line
    dtg_inverted = [-d for d in dtgs]
    dtg_data = [[float(t), float(d_inv)] for t, d_inv in zip(temps, dtg_inverted)]
    
    # Calculate Residue at ~800°C
    res_temp, res_weight = get_nearest_point(temps, weights, 800.0)
    
    # Calculate Peak above 150°C
    peak_temp, peak_dtg_raw = find_peak_above_temp(temps, dtgs, 150.0)
    
    # Build Markers and Labels
    mark_points = []
    
    if res_weight is not None:
        mark_points.append({
            "coord": [res_temp, res_weight],
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#000000"},
            "label": {
                "show": True,
                "formatter": f"Residue {res_weight:.1f}%",
                "position": "top",
                "offset": [0, -5],
                "color": "#000000",
                "fontSize": 10,
                "fontFamily": "Noto Sans CJK KR"
            }
        })
        
    if peak_temp is not None:
        # For the peak marker on the DTG curve (inverted)
        y_val_chart = -peak_dtg_raw
        mark_points.append({
            "coord": [peak_temp, y_val_chart],
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{int(peak_temp)} °C",
                "position": "top",
                "offset": [0, -5],
                "color": "#c0392b",
                "fontSize": 10,
                "fontFamily": "Noto Sans CJK KR"
            }
        })

    # Construct ECharts Option
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "2%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16,
                "fontWeight": "bold"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": ["Weight (%)", "DTG"],
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
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {
                "formatter": "{value} °C"
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
                "axisLabel": {
                    "formatter": "{value} %"
                },
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#ccc"
                    }
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
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
                "data": weight_data,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {
                    "color": "#000000",
                    "width": 2.5
                },
                "markPoint": {
                    "data": mark_points
                }
            },
            {
                "name": "DTG",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 1.5,
                    "type": "dashed"
                }
            }
        ]
    }
    
    return option

figures = []

# Read Excel file
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

for name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=name)
    opt = process_sheet(df, name)
    if opt:
        figures.append({
            "name": name.replace(" ", "_"),
            "option": opt,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

output = {"figures": figures}
print(json.dumps(output, ensure_ascii=False))
