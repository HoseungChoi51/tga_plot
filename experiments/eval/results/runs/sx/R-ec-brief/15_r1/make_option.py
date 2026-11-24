import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def read_sheet(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    # Identify columns based on common TGA naming conventions or position if names are ambiguous
    # Based on preview: A=Time, B=Temperature, C=Weight(%), D=D.W(%/C)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    cols = df.columns.tolist()
    
    # Try to find by name first
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl or 'temperature' in cl:
            temp_col = c
        elif 'weight' in cl or 'wt' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            dtg_col = c
            
    # Fallback to positional if names not found (assuming standard order Time, Temp, Weight, DTG)
    if temp_col is None and len(cols) > 1: temp_col = cols[1]
    if weight_col is None and len(cols) > 2: weight_col = cols[2]
    if dtg_col is None and len(cols) > 3: dtg_col = cols[3]
    
    if temp_col is None or weight_col is None:
        return None
        
    x_data = df[temp_col].dropna().values
    y1_data = df[weight_col].dropna().values
    y2_data = df[dtg_col].dropna().values if dtg_col else []
    
    # Align lengths just in case of NaN drops causing mismatch, though usually they are row-aligned
    min_len = min(len(x_data), len(y1_data))
    x_data = x_data[:min_len]
    y1_data = y1_data[:min_len]
    if len(y2_data) >= min_len:
        y2_data = y2_data[:min_len]
    else:
        y2_data = []
        
    return {
        "x": x_data.tolist(),
        "y1": y1_data.tolist(),
        "y2": y2_data.tolist(),
        "name": sheet_name
    }

def get_residue_and_peak(data_dict):
    """
    Calculates residue at ~800C and peak temp > 150C from raw data arrays.
    Returns (residue_temp, residue_val, peak_temp, peak_val_negated_for_plot)
    Note: Peak value for label is the temperature. The marker on plot needs coords.
    """
    x = np.array(data_dict['x'])
    y1 = np.array(data_dict['y1'])
    y2_raw = np.array(data_dict['y2'])
    
    # Residue at nearest 800C
    idx_800 = np.argmin(np.abs(x - 800))
    res_x = x[idx_800]
    res_y = y1[idx_800]
    
    # Peak: highest DTG peak above 150C. 
    # DTG is negative during mass loss. "Highest peak" usually means most negative (largest magnitude).
    # We want the point where derivative is minimum (most negative) in the region T > 150.
    mask = x > 150
    if not np.any(mask):
        return (res_x, res_y, None, None, None)
        
    y2_masked = y2_raw[mask]
    x_masked = x[mask]
    
    if len(y2_masked) == 0:
         return (res_x, res_y, None, None, None)
         
    # Find index of minimum value (most negative) in masked array
    min_idx = np.argmin(y2_masked)
    peak_x = x_masked[min_idx]
    peak_y_raw = y2_masked[min_idx] # This is negative
    
    # For plotting markers on Y2 axis, we use the negated value so it points up
    peak_y_plot = -peak_y_raw
    
    return (res_x, res_y, peak_x, peak_y_raw, peak_y_plot)

# Load all sheets
xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

all_series = []
annotations = []
legend_data = []

colors_y1 = ['#1f4e9c', '#2ecc71', '#e67e22', '#9b59b6', '#34495e']
colors_y2 = ['#c0392b', '#f1c40f', '#e74c3c', '#8e44ad', '#2c3e50']

for i, s_name in enumerate(sheet_names):
    data = read_sheet(DATA_FILE, s_name)
    if not data: continue
    
    x = data['x']
    y1 = data['y1']
    y2 = data['y2']
    
    # Calculate stats for annotations
    res_x, res_y, pk_x, pk_y_raw, pk_y_plot = get_residue_and_peak(data)
    
    # Series 1: Weight (%) -> Left Axis (yAxisIndex 0)
    color1 = colors_y1[i % len(colors_y1)]
    series_weight = {
        "name": f"{s_name} Weight",
        "type": "line",
        "data": list(zip(x, y1)),
        "yAxisIndex": 0,
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {"color": color1, "width": 2},
        "itemStyle": {"color": color1}
    }
    all_series.append(series_weight)
    
    # Series 2: DTG (-DTG) -> Right Axis (yAxisIndex 1)
    # Negate DTG so peaks point up
    y2_negated = [-val for val in y2]
    color2 = colors_y2[i % len(colors_y2)]
    series_dtg = {
        "name": f"{s_name} -DTG",
        "type": "line",
        "data": list(zip(x, y2_negated)),
        "yAxisIndex": 1,
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {"color": color2, "width": 2, "type": "dashed"},
        "itemStyle": {"color": color2}
    }
    all_series.append(series_dtg)
    
    # Legend entry (just one per sheet group usually, but ECharts legend works on series names. 
    # To keep legend clean, we might hide individual series from legend and add custom legend items? 
    # Or simpler: Let ECharts handle it, but that creates 2 entries per sheet. 
    # Better approach for "overlaid": Use custom legend formatter or just accept multiple entries.
    # Given constraints, I will let them appear but maybe group visually via color consistency.
    # Actually, standard practice for overlaid plots is often just showing the curves. 
    # I'll include them in legend but users can toggle.
    
    # Annotations
    if res_x is not None:
        # Marker for residue
        annotations.append({
            "coord": [res_x, res_y],
            "value": f"Residue {res_y:.1f}%",
            "symbol": "circle",
            "symbolSize": 6,
            "itemStyle": {"color": color1},
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}",
                "color": "#333",
                "fontSize": 10,
                "backgroundColor": "rgba(255,255,255,0.7)",
                "padding": [2, 4]
            }
        })
        
    if pk_x is not None:
        # Marker for peak on Y2 axis (negated value)
        # Need to map back to correct Y2 coordinate for the markPoint
        # The data in series is (x, -DTG). So the coord should be [pk_x, pk_y_plot]
        annotations.append({
            "coord": [pk_x, pk_y_plot],
            "value": f"{pk_x:.0f} °C",
            "symbol": "diamond",
            "symbolSize": 6,
            "itemStyle": {"color": color2},
            "label": {
                "show": True,
                "position": "right",
                "formatter": "{c}",
                "color": "#333",
                "fontSize": 10,
                "backgroundColor": "rgba(255,255,255,0.7)",
                "padding": [2, 4]
            }
        })

# Determine Axis Ranges dynamically
all_x = []
all_y1 = []
all_y2 = [] # These are already negated in series construction logic above? No, raw was passed to calc, negated for series.
             # But for range calculation, we need the plotted values.

for s in all_series:
    if s['yAxisIndex'] == 0:
        all_x.extend([p[0] for p in s['data']])
        all_y1.extend([p[1] for p in s['data']])
    else:
        all_x.extend([p[0] for p in s['data']])
        all_y2.extend([p[1] for p in s['data']]) # These are -DTG

if not all_x:
    print(json.dumps({"figures": []}))
else:
    x_min, x_max = min(all_x), max(all_x)
    y1_min, y1_max = min(all_y1), max(all_y1)
    y2_min, y2_max = min(all_y2), max(all_y2)
    
    # Add some padding
    pad_x = (x_max - x_min) * 0.05
    pad_y1 = (y1_max - y1_min) * 0.05
    pad_y2 = (y2_max - y2_min) * 0.05
    
    option = {
        "title": {
            "text": "TGA Analysis Overlap",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "formatter": None # Default formatter handles multi-series well
        },
        "legend": {
            "data": [s["name"] for s in all_series],
            "top": "bottom",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
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
            "min": x_min - pad_x,
            "max": x_max + pad_x,
            "axisLine": {"onZero": False},
            "splitLine": {"show": True, "lineStyle": {"color": "#eee"}},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y1_min - pad_y1,
                "max": y1_max + pad_y1,
                "position": "left",
                "axisLine": {"onZero": False},
                "splitLine": {"show": True, "lineStyle": {"color": "#eee"}},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y2_min - pad_y2,
                "max": y2_max + pad_y2,
                "position": "right",
                "axisLine": {"onZero": False},
                "splitLine": {"show": False},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            }
        ],
        "series": all_series
    }
    
    # Add MarkPoints for annotations
    # Grouping markPoints into a dummy series or attaching to existing?
    # Attaching to existing series requires matching yAxisIndex.
    # It's cleaner to create a separate scatter series for markers if needed, 
    # but markPoint is better for labels.
    # Since annotations mix axes, I'll distribute them.
    
    for ann in annotations:
        coord = ann['coord']
        # Determine which series this belongs to based on Y value range? 
        # No, we know: Residue is Y1, Peak is Y2.
        # We can add a global graphic layer or just attach to specific series indices.
        pass 

    # Re-attaching annotations properly
    # Create two helper series for marks to avoid cluttering main lines with markPoint config complexity across different axes
    # Actually, simpler: Just put markPoint in the corresponding series type.
    
    # Reset series to clear any potential issues, then re-add with markPoints
    final_series = []
    
    # Helper to identify which series index corresponds to which sheet/type
    # We appended Weight then DTG for each sheet.
    # Index 0: Sheet 1 Weight, Index 1: Sheet 1 DTG
    # Index 2: Sheet 2 Weight, Index 3: Sheet 2 DTG
    
    # Map annotation to series index
    # Residue -> Weight series (even indices)
    # Peak -> DTG series (odd indices)
    
    weight_marks = {} # key: series_index, value: list of markpoints
    dtg_marks = {}
    
    # We need to know which sheet index generated the annotation. 
    # The loop earlier didn't store the index explicitly in the annotation object.
    # Let's redo the annotation collection slightly more robustly or infer.
    
    # Re-calculate annotations inside the loop structure isn't possible now without refactoring entire script flow.
    # Instead, I will rely on the fact that `all_series` is ordered.
    # I will iterate through `all_series` and inject markPoints based on recalculated values for that specific series data.
    
    final_series = []
    for i, s in enumerate(all_series):
        new_s = dict(s) # copy
        if s['yAxisIndex'] == 0: # Weight series
            # Recalculate residue for this specific data
            x_arr = np.array([p[0] for p in s['data']])
            y_arr = np.array([p[1] for p in s['data']])
            if len(x_arr) > 0:
                idx = np.argmin(np.abs(x_arr - 800))
                rx, ry = x_arr[idx], y_arr[idx]
                new_s['markPoint'] = {
                    "data": [{
                        "coord": [float(rx), float(ry)],
                        "value": f"Residue {ry:.1f}%",
                        "symbol": "circle",
                        "symbolSize": 6,
                        "itemStyle": {"color": s['itemStyle']['color']},
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": "{c}",
                            "color": "#333",
                            "fontSize": 10,
                            "backgroundColor": "rgba(255,255,255,0.7)",
                            "padding": [2, 4]
                        }
                    }]
                }
        else: # DTG series
            # Recalculate peak for this specific data
            # Data is (Temp, -DTG)
            x_arr = np.array([p[0] for p in s['data']])
            y_arr = np.array([p[1] for p in s['data']]) # These are positive peaks
            
            # Mask > 150
            mask = x_arr > 150
            if np.any(mask):
                x_m = x_arr[mask]
                y_m = y_arr[mask]
                # Highest peak = Max value in -DTG (which corresponds to most negative original DTG)
                idx = np.argmax(y_m)
                px, py = x_m[idx], y_m[idx]
                
                new_s['markPoint'] = {
                    "data": [{
                        "coord": [float(px), float(py)],
                        "value": f"{px:.0f} °C",
                        "symbol": "diamond",
                        "symbolSize": 6,
                        "itemStyle": {"color": s['itemStyle']['color']},
                        "label": {
                            "show": True,
                            "position": "right",
                            "formatter": "{c}",
                            "color": "#333",
                            "fontSize": 10,
                            "backgroundColor": "rgba(255,255,255,0.7)",
                            "padding": [2, 4]
                        }
                    }]
                }
        final_series.append(new_s)
        
    option['series'] = final_series

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

