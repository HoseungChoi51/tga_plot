import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def make_tga_plot(df, sheet_name):
    # Extract columns based on standard TGA structure from preview
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2_raw = df[dtg_col].values
    
    # Prepare data for ECharts (list of [x, y] pairs)
    data_weight = [[float(t), float(w)] for t, w in zip(x, y1)]
    # Multiply DTG by -1 so peaks point up
    data_dtg = [[float(t), float(-d)] for t, d in zip(x, y2_raw)]
    
    # Calculate Residue at 800°C
    # Find index closest to 800
    idx_800 = np.argmin(np.abs(x - 800))
    residue_val = float(y1[idx_800])
    residue_temp = float(x[idx_800])
    
    # Calculate Peak Temperature (highest DTG peak above 150°C)
    # Filter for temp > 150 and find max of (-DTG) i.e., min of raw DTG since we inverted? 
    # Wait, user said "multiplied by -1 so its peaks point up". So the value plotted is -DTG.
    # We want the highest peak of the *plotted* DTG curve (which corresponds to most negative raw DTG).
    mask = x > 150
    if np.any(mask):
        # Find index where -y2_raw is maximum among masked points
        # Equivalent to finding minimum of y2_raw among masked points
        masked_indices = np.where(mask)[0]
        # Get values of -y2_raw for these indices
        neg_dtg_vals = -y2_raw[masked_indices]
        max_neg_idx_local = np.argmax(neg_dtg_vals)
        peak_idx = masked_indices[max_neg_idx_local]
        peak_temp = float(x[peak_idx])
        peak_val_plotted = float(-y2_raw[peak_idx])
    else:
        peak_temp = None
        peak_val_plotted = None

    # Determine Axis Ranges dynamically but with some padding
    x_min = float(min(x.min(), 30))
    x_max = float(max(x.max(), 900))
    
    y1_min = float(y1.min())
    y1_max = float(y1.max())
    y1_range = y1_max - y1_min
    y1_pad = y1_range * 0.1
    y1_axis_min = max(0.0, y1_min - y1_pad) # Weight usually doesn't go below 0 physically, but let's keep it safe
    y1_axis_max = float(y1_max + y1_pad)
    
    # For DTG (inverted), range is around 0 to positive peak
    dtg_plot_vals = -y2_raw
    y2_min = float(dtg_plot_vals.min())
    y2_max = float(dtg_plot_vals.max())
    y2_range = y2_max - y2_min
    y2_pad = y2_range * 0.1
    y2_axis_min = float(y2_min - y2_pad)
    y2_axis_max = float(y2_max + y2_pad)
    
    # Ensure 0 is visible or close to it for DTG if possible, often DTG oscillates around 0
    if y2_axis_min > 0: y2_axis_min = -abs(y2_max)*0.1
    if y2_axis_max < 0: y2_axis_max = abs(y2_min)*0.1

    series_list = [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": data_weight,
            "itemStyle": {"color": "#1f4e9c"},
            "lineStyle": {"width": 2},
            "symbol": "none",
            "smooth": False
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_dtg,
            "itemStyle": {"color": "#c0392b"},
            "lineStyle": {"width": 2},
            "symbol": "none",
            "smooth": False
        }
    ]
    
    # Add Markers for Residue and Peak
    mark_points = []
    labels = []
    
    # Residue Marker
    mark_points.append({
        "coord": [residue_temp, residue_val],
        "symbolSize": 6,
        "itemStyle": {"color": "#1f4e9c"}
    })
    labels.append({
        "position": "top",
        "formatter": f"Residue {residue_val:.1f}%",
        "style": {"fill": "#1f4e9c", "fontSize": 10}
    })
    
    # Peak Marker
    if peak_temp is not None:
        mark_points.append({
            "coord": [peak_temp, peak_val_plotted],
            "symbolSize": 6,
            "itemStyle": {"color": "#c0392b"}
        })
        labels.append({
            "position": "top",
            "formatter": f"{int(round(peak_temp))} °C",
            "style": {"fill": "#c0392b", "fontSize": 10}
        })
        
    # Attach markPoint to the respective series? 
    # ECharts markPoint is usually attached to a specific series.
    # We'll attach residue to weight series and peak to dtg series separately or use scatter series.
    # Using separate scatter series is cleaner for markers.
    
    scatter_data_residue = [{
        "value": [residue_temp, residue_val],
        "label": {
            "show": True,
            "formatter": f"Residue {residue_val:.1f}%",
            "position": "top",
            "color": "#1f4e9c",
            "fontSize": 10
        },
        "itemStyle": {"color": "#1f4e9c"}
    }]
    
    series_list.append({
        "name": "Residue Marker",
        "type": "scatter",
        "yAxisIndex": 0,
        "data": scatter_data_residue,
        "symbolSize": 8,
        "silent": True,
        "zlevel": 10
    })
    
    if peak_temp is not None:
        scatter_data_peak = [{
            "value": [peak_temp, peak_val_plotted],
            "label": {
                "show": True,
                "formatter": f"{int(round(peak_temp))} °C",
                "position": "top",
                "color": "#c0392b",
                "fontSize": 10
            },
            "itemStyle": {"color": "#c0392b"}
        }]
        
        series_list.append({
            "name": "Peak Marker",
            "type": "scatter",
            "yAxisIndex": 1,
            "data": scatter_data_peak,
            "symbolSize": 8,
            "silent": True,
            "zlevel": 10
        })

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
            "axisPointer": {"type": "cross"}
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
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 25,
            "min": x_min,
            "max": x_max,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y1_axis_min,
                "max": y1_axis_max,
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y2_axis_min,
                "max": y2_axis_max,
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {"show": False}
            }
        ],
        "series": series_list
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
xl_file = pd.ExcelFile(DATA_FILE)
for sheet_name in xl_file.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    fig = make_tga_plot(df, sheet_name)
    figures.append(fig)

output = {"figures": figures}
print(json.dumps(output))
