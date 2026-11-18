import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def make_tga_plot(df, sheet_name):
    x_col = "Temperature"
    y1_col = "Weight(%)"
    y2_col = "D.W(%/C)"
    
    # Extract data
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg_raw = df[y2_col].values
    
    # Invert DTG so peaks point up
    dtg = -dtg_raw
    
    # Find residue at 800°C (nearest point)
    mask_800 = (temp >= 750) & (temp <= 850)
    if mask_800.any():
        idx_800 = np.argmin(np.abs(temp[mask_800] - 800))
        actual_idx = np.where(mask_800)[0][idx_800]
        residue_val = weight[actual_idx]
        residue_temp = temp[actual_idx]
    else:
        # Fallback to last point if no data near 800
        residue_val = weight[-1]
        residue_temp = temp[-1]
    
    # Find peak in DTG above 150°C
    mask_peak = temp > 150
    if mask_peak.any():
        dtg_above_150 = dtg[mask_peak]
        temps_above_150 = temp[mask_peak]
        max_dtg_idx = np.argmax(dtg_above_150)
        peak_temp = temps_above_150[max_dtg_idx]
        peak_dtg_val = dtg_above_150[max_dtg_idx]
    else:
        peak_temp = None
        peak_dtg_val = None
    
    # Prepare series data
    weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    dtg_data = [[float(t), float(d)] for t, d in zip(temp, dtg)]
    
    # Markers for annotations
    markers = []
    annotations = []
    
    # Residue marker and label
    markers.append({
        "coord": [float(residue_temp), float(residue_val)],
        "symbol": "circle",
        "symbolSize": 6,
        "itemStyle": {"color": "#1f4e9c"}
    })
    annotations.append({
        "type": "text",
        "x": "center",
        "y": "top",
        "text": f"Residue {residue_val:.1f}%",
        "style": {"fontSize": 12, "fill": "#333"},
        "position": "insideRight",
        "distance": 10
    })
    
    # Peak marker and label
    if peak_temp is not None:
        markers.append({
            "coord": [float(peak_temp), float(peak_dtg_val)],
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"}
        })
        annotations.append({
            "type": "text",
            "x": "center",
            "y": "top",
            "text": f"{peak_temp:.0f} °C",
            "style": {"fontSize": 12, "fill": "#333"},
            "position": "insideLeft",
            "distance": 10
        })
    
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 14}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "-DTG"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"}
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
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": weight_data,
                "yAxisIndex": 0,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#000000",
                    "width": 2.5
                },
                "markPoint": {
                    "data": markers[:1],
                    "label": {"show": False}
                }
            },
            {
                "name": "-DTG",
                "type": "line",
                "data": dtg_data,
                "yAxisIndex": 1,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 1.5,
                    "type": "dashed"
                },
                "markPoint": {
                    "data": markers[1:],
                    "label": {"show": False}
                }
            }
        ]
    }
    
    return option

# Load Excel file
xls = pd.ExcelFile(DATA_FILE)
figures = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    option = make_tga_plot(df, sheet_name)
    figures.append({
        "name": sheet_name.replace(" ", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

result = {"figures": figures}
print(json.dumps(result, ensure_ascii=False))
