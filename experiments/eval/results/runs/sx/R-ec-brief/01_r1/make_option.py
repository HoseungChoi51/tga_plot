import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def get_nearest_point(df, x_col, y_col, target_x):
    """Find the row in df where x_col is closest to target_x."""
    if df.empty:
        return None, None
    idx = (df[x_col] - target_x).abs().idxmin()
    # Convert numpy types to python native types for JSON serialization
    return float(df.loc[idx, x_col]), float(df.loc[idx, y_col])

def process_sheet(sheet_name, df):
    cols = df.columns.tolist()
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or ('derivative' in cl and 'weight' in cl):
            dtg_col = c
            
    if temp_col is None and len(cols) >= 2: temp_col = cols[1]
    if weight_col is None and len(cols) >= 3: weight_col = cols[2]
    if dtg_col is None and len(cols) >= 4: dtg_col = cols[3]

    if not all([temp_col, weight_col, dtg_col]):
        return None

    df_clean = df[[temp_col, weight_col, dtg_col]].dropna()
    
    if df_clean.empty:
        return None

    temps = [float(t) for t in df_clean[temp_col].tolist()]
    weights = [float(w) for w in df_clean[weight_col].tolist()]
    dtgs_raw = [float(d) for d in df_clean[dtg_col].tolist()]
    
    dtgs_inv = [-x for x in dtgs_raw]
    
    residue_temp, residue_weight = get_nearest_point(df_clean, temp_col, weight_col, 800.0)
    
    peak_temp_val = None
    peak_dtg_val = None
    
    # Filter for temp > 150
    filtered_indices = [i for i, t in enumerate(temps) if t > 150]
    
    if filtered_indices:
        max_idx_in_filtered = -1
        max_dtg_val = -float('inf')
        
        for i in filtered_indices:
            if dtgs_inv[i] > max_dtg_val:
                max_dtg_val = dtgs_inv[i]
                max_idx_in_filtered = i
        
        if max_idx_in_filtered != -1:
            peak_temp_val = temps[max_idx_in_filtered]
            peak_dtg_val = dtgs_inv[max_idx_in_filtered]

    series_data_weight = [[t, w] for t, w in zip(temps, weights)]
    series_data_dtg = [[t, d] for t, d in zip(temps, dtgs_inv)]
    
    mark_points_weight = []
    if residue_temp is not None:
        mark_points_weight.append({
            "coord": [residue_temp, residue_weight],
            "symbolSize": 8,
            "label": {
                "show": True,
                "formatter": f"Residue {residue_weight:.1f}%",
                "position": "top",
                "fontSize": 12,
                "color": "#1f4e9c"
            },
            "itemStyle": {"color": "#1f4e9c"}
        })
        
    mark_points_dtg = []
    if peak_temp_val is not None and peak_dtg_val is not None:
        mark_points_dtg.append({
            "coord": [peak_temp_val, peak_dtg_val],
            "symbolSize": 8,
            "label": {
                "show": True,
                "formatter": f"{int(peak_temp_val)} °C",
                "position": "top",
                "fontSize": 12,
                "color": "#c0392b"
            },
            "itemStyle": {"color": "#c0392b"}
        })

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
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
            "name": "Temperature (°C)",
            "type": "value",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLine": {"onZero": False},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "type": "value",
                "position": "left",
                "nameLocation": "middle",
                "nameGap": 40,
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}}
            },
            {
                "name": "DTG (%/°C)",
                "type": "value",
                "position": "right",
                "nameLocation": "middle",
                "nameGap": 40,
                "splitLine": {"show": False},
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": series_data_weight,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": mark_points_weight
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": series_data_dtg,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": mark_points_dtg
                }
            }
        ]
    }
    
    return option

def main():
    figures = []
    
    xls = pd.ExcelFile(DATA_FILE)
    sheet_names = xls.sheet_names
    
    for i, sheet_name in enumerate(sheet_names):
        df = pd.read_excel(xls, sheet_name=sheet_name)
        opt = process_sheet(sheet_name, df)
        if opt:
            fig_entry = {
                "name": f"plot_{i+1}",
                "option": opt,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
            figures.append(fig_entry)
            
    result = {"figures": figures}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
