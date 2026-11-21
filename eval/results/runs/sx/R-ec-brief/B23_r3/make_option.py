import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def get_tga_data(df):
    # Identify columns based on the preview structure or standard names
    cols = df.columns.tolist()
    
    # Heuristic to find x, y1 (weight), y2 (dtg)
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temperature' in c_lower or 'temp' in c_lower:
            x_col = c
        elif 'weight' in c_lower and 'deriv' not in c_lower and 'dtg' not in c_lower:
            y1_col = c
        elif 'deriv' in c_lower or 'dtg' in c_lower:
            y2_col = c
            
    if x_col is None or y1_col is None or y2_col is None:
        return None
        
    data = df[[x_col, y1_col, y2_col]].dropna()
    if len(data) == 0:
        return None
        
    temps = data[x_col].values
    weights = data[y1_col].values
    dtgs = data[y2_col].values
    
    return temps, weights, dtgs

def calculate_metrics(temps, weights, dtgs):
    # Residue at nearest 800 C
    idx_800 = np.argmin(np.abs(temps - 800))
    residue_val = weights[idx_800]
    residue_temp = temps[idx_800]
    
    # Peak DTG above 150 C
    mask = temps > 150
    if np.any(mask):
        dtgs_masked = dtgs[mask]
        temps_masked = temps[mask]
        # Find index of minimum DTG (most negative) because we plot -DTG so peak is max positive
        min_dtg_idx = np.argmin(dtgs_masked)
        peak_temp = temps_masked[min_dtg_idx]
        peak_val = dtgs_masked[min_dtg_idx]
    else:
        peak_temp = None
        peak_val = None
        
    return residue_val, residue_temp, peak_temp, peak_val

def create_series(name, temps, weights, dtgs, color):
    # Prepare data for ECharts: [[x, y], ...]
    # Weight series (y1)
    weight_data = []
    for t, w in zip(temps, weights):
        weight_data.append([float(t), float(w)])
        
    # DTG series (y2), multiplied by -1 to point up
    dtg_data = []
    for t, d in zip(temps, dtgs):
        dtg_data.append([float(t), float(-d)])
        
    # Calculate metrics for labels
    residue_val, residue_temp, peak_temp, peak_val = calculate_metrics(temps, weights, dtgs)
    
    series_list = []
    
    # Weight Line
    series_list.append({
        "name": f"{name} Weight",
        "type": "line",
        "yAxisIndex": 0,
        "data": weight_data,
        "itemStyle": {"color": color},
        "lineStyle": {"width": 2, "color": color},
        "showSymbol": False,
        "smooth": False
    })
    
    # DTG Line
    series_list.append({
        "name": f"{name} DTG",
        "type": "line",
        "yAxisIndex": 1,
        "data": dtg_data,
        "itemStyle": {"color": color},
        "lineStyle": {"width": 1.5, "color": color, "opacity": 0.7},
        "showSymbol": False,
        "smooth": True
    })
    
    # Markers and Labels
    mark_points = []
    
    # Residue Marker
    if residue_temp is not None:
        mark_points.append({
            "coord": [float(residue_temp), float(residue_val)],
            "symbolSize": 6,
            "label": {
                "formatter": f"Residue {residue_val:.1f}%",
                "position": "top",
                "fontSize": 9,
                "color": "#333"
            }
        })
        
    # Peak Marker
    if peak_temp is not None and peak_val is not None:
        # Note: peak_val is original DTG (negative). We plotted -DTG. 
        # So Y coord for marker on DTG line is -peak_val
        mark_points.append({
            "coord": [float(peak_temp), float(-peak_val)],
            "symbolSize": 6,
            "label": {
                "formatter": f"{peak_temp:.0f} °C",
                "position": "right",
                "fontSize": 9,
                "color": "#333"
            }
        })
        
    if mark_points:
        series_list[0]["markPoint"] = {
            "data": mark_points,
            "symbol": "circle",
            "itemStyle": {"color": color}
        }
        
    return series_list

# Load Excel file
xl = pd.ExcelFile(DATA_FILE)
sheets = xl.sheet_names

all_series = []
colors = {
    "Raw": "#000000",       # Black
    "Acid-washed": "#1f4e9c", # Blue
    "Annealed": "#c0392b"     # Red
}

for sheet_name in sheets:
    df = xl.parse(sheet_name)
    result = get_tga_data(df)
    if result:
        temps, weights, dtgs = result
        # Determine color: check if sheet name matches keys in colors dict approximately
        color = "#888888" # Default gray
        for key, val in colors.items():
            if key.lower() in sheet_name.lower():
                color = val
                break
        
        s = create_series(sheet_name, temps, weights, dtgs, color)
        all_series.extend(s)

# Construct ECharts Option
option = {
    "title": {
        "text": "TGA Comparison: Raw, Acid-washed, Annealed",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": "{a0}: {c0}<br/>{a1}: {c1}" # Simplified tooltip
    },
    "legend": {
        "data": [],
        "top": "10%",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
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
        "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": "#eee"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "nameLocation": "middle",
            "nameGap": 40,
            "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": "#eee"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "nameLocation": "middle",
            "nameGap": 40,
            "splitLine": {"show": False},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": all_series
}

# Update legend data with series names
legend_data = [s["name"] for s in all_series]
option["legend"]["data"] = legend_data

output = {
    "figures": [
        {
            "name": "tga_comparison",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
