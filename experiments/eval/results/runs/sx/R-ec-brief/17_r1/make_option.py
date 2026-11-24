import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def make_tga_chart(df, sheet_name):
    """Create an ECharts option for a TGA plot from a DataFrame."""
    # Identify columns
    temp_col = None
    weight_col = None
    dtg_col = None
    
    cols = df.columns.tolist()
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl or '온도' in cl:
            temp_col = c
        elif 'weight' in cl or '무게' in cl or 'wt%' in cl or 'w(%)' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl or 'deriv' in cl:
            dtg_col = c
    
    if temp_col is None:
        temp_col = cols[1]  # Fallback to second column
    if weight_col is None:
        weight_col = cols[2]
    if dtg_col is None:
        dtg_col = cols[3]
    
    temps = df[temp_col].values.astype(float)
    weights = df[weight_col].values.astype(float)
    dtgs = df[dtg_col].values.astype(float)
    
    # Negate DTG so peaks point up
    dtgs_neg = -dtgs
    
    # Find residue at ~800°C (or nearest available temperature <= max)
    target_temp = 800.0
    mask_valid = temps <= max(temps)
    valid_temps = temps[mask_valid]
    valid_weights = weights[mask_valid]
    
    if len(valid_temps) > 0:
        idx_residue = np.argmin(np.abs(valid_temps - target_temp))
        residue_temp = valid_temps[idx_residue]
        residue_weight = valid_weights[idx_residue]
    else:
        residue_temp = temps[-1]
        residue_weight = weights[-1]
    
    # Find highest DTG peak above 150°C
    mask_peak = (temps > 150) & (dtgs_neg > 0)
    if np.any(mask_peak):
        dtgs_neg_filtered = dtgs_neg.copy()
        dtgs_neg_filtered[~mask_peak] = -np.inf
        idx_peak = np.argmax(dtgs_neg_filtered)
        peak_temp = temps[idx_peak]
        peak_dtg_val = dtgs_neg[idx_peak]
    else:
        peak_temp = None
        peak_dtg_val = None
    
    # Build series data
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    dtg_data = [[float(t), float(d)] for t, d in zip(temps, dtgs_neg)]
    
    # Markers for residue and peak
    marker_series = []
    mark_points = []
    
    # Residue marker
    mark_points.append({
        "coord": [float(residue_temp), float(residue_weight)],
        "name": f"Residue {residue_weight:.1f}%",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_weight:.1f}%",
            "position": "top",
            "fontSize": 11,
            "color": "#1f4e9c"
        }
    })
    
    # Peak marker
    if peak_temp is not None:
        mark_points.append({
            "coord": [float(peak_temp), float(peak_dtg_val)],
            "name": f"{peak_temp:.0f} °C",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "fontSize": 11,
                "color": "#c0392b"
            }
        })
    
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {
                "fontSize": 16,
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "DTG (-%/°C)"],
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
            "bottom": "12%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 45,
                "position": "left",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "DTG (-%/°C)",
                "nameLocation": "middle",
                "nameGap": 45,
                "position": "right",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": weight_data,
                "smooth": False,
                "lineStyle": {"width": 2, "color": "#1f4e9c"},
                "showSymbol": False,
                "markPoint": {
                    "data": [mp for mp in mark_points if mp["itemStyle"]["color"] == "#1f4e9c"]
                }
            },
            {
                "name": "DTG (-%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": False,
                "lineStyle": {"width": 2, "color": "#c0392b"},
                "showSymbol": False,
                "markPoint": {
                    "data": [mp for mp in mark_points if mp["itemStyle"]["color"] == "#c0392b"]
                }
            }
        ]
    }
    
    return option

def main():
    xls = pd.ExcelFile(DATA_FILE)
    figures = []
    
    # Figure size: width=8 inches, height=5 inches at 96 dpi => 768 x 480 px
    fig_width_px = int(8 * 96)   # 768
    fig_height_px = int(5 * 96)  # 480
    dpi = 600
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
        option = make_tga_chart(df, sheet_name)
        figures.append({
            "name": sheet_name.replace(" ", "_").replace("-", "_"),
            "option": option,
            "width": fig_width_px,
            "height": fig_height_px,
            "dpi": dpi,
            "formats": ["png"]
        })
    
    result = {"figures": figures}
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
