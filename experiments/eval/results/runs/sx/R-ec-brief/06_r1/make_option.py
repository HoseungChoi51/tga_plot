import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def make_tga_plot(df, sheet_name):
    # Extract data
    temp = df['Temperature'].values.astype(float)
    weight = df['Weight(%)'].values.astype(float)
    dtg = df['D.W(%/C)'].values.astype(float)
    
    # Calculate residue at 800°C (or nearest point if max temp < 800)
    max_temp = np.max(temp)
    target_residue_temp = 800.0
    idx_residue = np.argmin(np.abs(temp - target_residue_temp))
    residue_val = float(weight[idx_residue])
    residue_temp = float(temp[idx_residue])
    
    # Find highest DTG peak above 150°C
    mask = temp > 150.0
    if np.any(mask):
        dtg_above_150 = dtg[mask]
        temp_above_150 = temp[mask]
        # Peak is the most negative value in DTG (since we flip sign for plotting)
        min_dtg_idx = np.argmin(dtg_above_150)
        peak_temp = float(temp_above_150[min_dtg_idx])
        peak_dtg_val = float(dtg_above_150[min_dtg_idx])
    else:
        peak_temp = None
        peak_dtg_val = None

    # Prepare series data
    weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    dtg_data = [[float(t), float(-d)] for t, d in zip(temp, dtg)]  # Flip sign so peaks point up
    
    # Determine axis ranges
    y1_min = float(np.min(weight) * 0.95)
    y1_max = float(np.max(weight) * 1.02)
    
    # For flipped DTG (y2), we need to adjust range display or just let ECharts handle it?
    # Usually, if we plot -DTG, the values become positive where mass loss occurred.
    # Let's calculate range based on plotted values (-dtg)
    dtg_plotted = -dtg
    y2_plot_min = float(np.min(dtg_plotted))
    y2_plot_max = float(np.max(dtg_plotted))
    
    # Add some padding
    y2_range = y2_plot_max - y2_plot_min
    if y2_range == 0:
        y2_axis_min = y2_plot_min - 0.1
        y2_axis_max = y2_plot_max + 0.1
    else:
        y2_axis_min = y2_plot_min - y2_range * 0.1
        y2_axis_max = y2_plot_max + y2_range * 0.1
    
    x_min = float(np.min(temp))
    x_max = float(np.max(temp))
    
    # Build markers for residue and peak
    mark_points_weight = []
    mark_points_dtg = []
    
    if residue_val is not None:
        mark_points_weight.append({
            "coord": [residue_temp, residue_val],
            "name": f"Residue {residue_val:.1f}%",
            "value": f"Residue {residue_val:.1f}%",
            "symbol": "circle",
            "symbolSize": 6,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "fontSize": 10,
                "color": "#1f4e9c"
            }
        })
        
    if peak_temp is not None:
        # Peak marker on DTG curve (which is plotted as -dtg)
        # The value on the y2 axis for this point is -peak_dtg_val
        dtg_y_val = float(-peak_dtg_val)
        mark_points_dtg.append({
            "coord": [peak_temp, dtg_y_val],
            "name": f"{peak_temp:.0f} °C",
            "value": f"{peak_temp:.0f} °C",
            "symbol": "diamond",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "fontSize": 10,
                "color": "#c0392b"
            }
        })

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "2%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14,
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
            "show": False  # User requested to remove legend
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "10%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": x_min,
            "max": x_max,
            "axisLine": {"lineStyle": {"color": "#333"}},
            "splitLine": {
                "show": True,  # Grid on
                "lineStyle": {"color": "#eee", "type": "dashed"}
            },
            "axisTick": {"show": True},
            "axisLabel": {"fontSize": 10}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y1_min,
                "max": y1_max,
                "axisLine": {"lineStyle": {"color": "#1f4e9c"}},
                "splitLine": {
                    "show": True,  # Grid on
                    "lineStyle": {"color": "#eee", "type": "dashed"}
                },
                "axisTick": {"show": True},
                "axisLabel": {"fontSize": 10, "color": "#1f4e9c"}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": y2_axis_min,
                "max": y2_axis_max,
                "axisLine": {"lineStyle": {"color": "#c0392b"}},
                "splitLine": {"show": False},
                "axisTick": {"show": True},
                "axisLabel": {"fontSize": 10, "color": "#c0392b"}
            }
        ],
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "data": weight_data,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "yAxisIndex": 0,
                "markPoint": {
                    "data": mark_points_weight
                }
            },
            {
                "name": "DTG",
                "type": "line",
                "data": dtg_data,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "yAxisIndex": 1,
                "markPoint": {
                    "data": mark_points_dtg
                }
            }
        ]
    }
    
    return option

figures = []
xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    # Clean column names just in case
    df.columns = [str(c).strip() for c in df.columns]
    
    if 'Temperature' in df.columns and 'Weight(%)' in df.columns and 'D.W(%/C)' in df.columns:
        opt = make_tga_plot(df, sheet_name)
        figures.append({
            "name": sheet_name.replace(" ", "_"),
            "option": opt,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

output = {"figures": figures}
print(json.dumps(output))
