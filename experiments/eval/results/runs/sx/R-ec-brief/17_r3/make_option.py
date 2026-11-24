import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Figure size: 8 x 5 inches at 96 px/inch -> width=768, height=480
FIG_WIDTH = int(8 * 96)
FIG_HEIGHT = int(5 * 96)
DPI = 600

def find_nearest_value(temp_array, weight_array, target_temp):
    """Find the weight value at the temperature nearest to target_temp."""
    if len(temp_array) == 0:
        return None, None
    idx = np.argmin(np.abs(temp_array - target_temp))
    return temp_array[idx], weight_array[idx]

def find_dtg_peak(temp_array, dtg_array, min_temp=150.0):
    """Find the temperature of the highest DTG peak (most negative DTG) above min_temp."""
    # Filter data above min_temp
    mask = temp_array > min_temp
    if not np.any(mask):
        return None, None
    
    filtered_temp = temp_array[mask]
    filtered_dtg = dtg_array[mask]
    
    # The "peak" in TGA context usually refers to the maximum rate of mass loss,
    # which corresponds to the most negative DTG value.
    # We want the temperature where DTG is minimum (most negative).
    idx_min = np.argmin(filtered_dtg)
    return filtered_temp[idx_min], filtered_dtg[idx_min]

def process_sheet(sheet_name, df):
    # Identify columns based on standard TGA structure provided in preview
    # Assuming column names or positions are consistent with preview:
    # Time, Temperature, Weight(%), D.W(%/C)
    
    cols = df.columns.tolist()
    # Heuristic to find columns if names vary slightly, but using known names from preview first
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temp' in c_lower:
            temp_col = c
        elif 'weight' in c_lower and '%' in c_lower:
            weight_col = c
        elif 'd.w' in c_lower or 'dtg' in c_lower or ('derivative' in c_lower and 'weight' in c_lower):
            dtg_col = c
            
    # Fallback to position if names don't match well
    if temp_col is None and len(cols) >= 2: temp_col = cols[1]
    if weight_col is None and len(cols) >= 3: weight_col = cols[2]
    if dtg_col is None and len(cols) >= 4: dtg_col = cols[3]
    
    if temp_col is None or weight_col is None or dtg_col is None:
        return None

    temps = df[temp_col].dropna().values
    weights = df[weight_col].dropna().values
    dtgs = df[dtg_col].dropna().values
    
    # Ensure arrays are aligned by dropping rows where any of these are NaN
    valid_mask = ~(df[temp_col].isna() | df[weight_col].isna() | df[dtg_col].isna())
    temps = df.loc[valid_mask, temp_col].values
    weights = df.loc[valid_mask, weight_col].values
    dtgs = df.loc[valid_mask, dtg_col].values
    
    if len(temps) == 0:
        return None

    # Prepare series data
    # Weight Series (y1)
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # DTG Series (y2), multiplied by -1 so peaks point up
    dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
    
    # Calculate Residue (nearest to 800 C)
    res_temp, res_weight = find_nearest_value(temps, weights, 800.0)
    
    # Calculate Peak (highest DTG peak > 150 C)
    peak_temp, peak_val_orig = find_dtg_peak(temps, dtgs, min_temp=150.0)
    
    # Markers for labels
    mark_points = []
    if res_weight is not None:
        mark_points.append({
            "coord": [float(res_temp), float(res_weight)],
            "name": f"Residue {res_weight:.1f}%",
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": f"Residue {res_weight:.1f}%",
                "position": "top",
                "fontSize": 10,
                "color": "#1f4e9c"
            }
        })
        
    if peak_temp is not None:
        # Plot DTG peak on the right axis (y2). Remember we plotted -DTG.
        # So the y-value on the plot is -peak_val_orig
        plot_y_val = -peak_val_orig
        mark_points_dtg = [{
            "coord": [float(peak_temp), float(plot_y_val)],
            "name": f"{peak_temp:.0f} °C",
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "fontSize": 10,
                "color": "#c0392b"
            }
        }]
    else:
        mark_points_dtg = []

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
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
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            }
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "opacity": 0.5
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "position": "left",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "opacity": 0.5
                    }
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "position": "right",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
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
                "data": weight_data,
                "yAxisIndex": 0,
                "smooth": True,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "markPoint": {
                    "data": mark_points
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": dtg_data,
                "yAxisIndex": 1,
                "smooth": True,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#c0392b"
                },
                "markPoint": {
                    "data": mark_points_dtg
                }
            }
        ]
    }
    
    return {
        "name": sheet_name.replace(" ", "_").replace("/", "_"),
        "option": option,
        "width": FIG_WIDTH,
        "height": FIG_HEIGHT,
        "dpi": DPI,
        "formats": ["png"]
    }

figures = []
xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    fig_obj = process_sheet(sheet_name, df)
    if fig_obj:
        figures.append(fig_obj)

output = {
    "figures": figures
}

print(json.dumps(output, ensure_ascii=False))
