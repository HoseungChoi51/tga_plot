import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_tga_data(df):
    # Identify columns based on standard TGA structure or guessing from preview
    cols = df.columns.tolist()
    
    # Try to find Temperature, Weight, DTG
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
            
    # Fallbacks if names are not clear (based on typical order: Time, Temp, Weight, DTG)
    if temp_col is None and len(cols) > 1: temp_col = cols[1]
    if weight_col is None and len(cols) > 2: weight_col = cols[2]
    if dtg_col is None and len(cols) > 3: dtg_col = cols[3]
    
    if temp_col is None or weight_col is None:
        return None
        
    data = df[[temp_col, weight_col]].dropna()
    if dtg_col:
        data_dtg = df[[temp_col, dtg_col]].dropna()
    else:
        data_dtg = None
        
    return data, data_dtg, temp_col, weight_col, dtg_col

def process_sheet(sheet_name, df):
    res = get_tga_data(df)
    if res is None:
        return None
    
    data_w, data_dtg, t_col, w_col, d_col = res
    
    temps = data_w[t_col].values.astype(float)
    weights = data_w[w_col].values.astype(float)
    
    # Prepare series data for ECharts [x, y]
    weight_series_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    dtg_series_data = []
    peak_temp = None
    residue_800 = None
    
    if data_dtg is not None:
        temps_d = data_dtg[t_col].values.astype(float)
        dtgs = data_dtg[d_col].values.astype(float)
        
        # Multiply by -1 so peaks point up
        dtgs_pos = [-1 * d for d in dtgs]
        dtg_series_data = [[float(t), float(d)] for t, d in zip(temps_d, dtgs_pos)]
        
        # Find Peak: highest DTG peak above 150 C
        mask_peak = (temps_d > 150) & (np.array(dtgs_pos) > 0)
        if np.any(mask_peak):
            idx_max = np.argmax(np.where(mask_peak, dtgs_pos, -np.inf))
            peak_temp = float(temps_d[idx_max])
            
    # Find Residue at nearest 800 C
    if len(temps) > 0:
        idx_res = int(np.argmin(np.abs(temps - 800)))
        residue_800 = float(weights[idx_res])
        residue_temp = float(temps[idx_res])
    else:
        residue_temp = None

    # Build Option
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
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
            "splitLine": {"show": False},
            "axisTick": {"show": True},
            "axisLabel": {
                "formatter": "{value}",
                "interval": 100 # Tick interval 100
            },
            "min": 0,
            "max": 900
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "splitLine": {"show": True, "lineStyle": {"color": "#ccc"}},
                "axisTick": {"show": True}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "position": "right",
                "splitLine": {"show": False},
                "axisTick": {"show": True},
                "min": -0.05, # User request: range -0.05 ~ 1.2
                "max": 1.2
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": weight_series_data,
                "itemStyle": {"color": "#1f4e9c"},
                "lineStyle": {"width": 2},
                "symbol": "none",
                "markPoint": {}
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_series_data,
                "itemStyle": {"color": "#c0392b"},
                "lineStyle": {"width": 2},
                "symbol": "none",
                "markPoint": {}
            }
        ]
    }
    
    # Add Markers for Residue and Peak
    mark_points_weight = []
    mark_points_dtg = []
    
    if residue_800 is not None and residue_temp is not None:
        mark_points_weight.append({
            "coord": [residue_temp, residue_800],
            "name": f"Residue {residue_800:.1f}%",
            "symbol": "circle",
            "symbolSize": 6,
            "label": {
                "show": True,
                "formatter": f"Residue {residue_800:.1f}%",
                "position": "right",
                "distance": 5,
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10,
                "color": "#1f4e9c"
            }
        })
        
    if peak_temp is not None:
        # Need the value of DTG at peak_temp to place marker correctly on y2
        # Since we multiplied by -1, find the index in original data or search in dtg_series_data
        # dtg_series_data contains [temp, -dtg]
        peak_val = None
        for item in dtg_series_data:
            if abs(item[0] - peak_temp) < 0.1:
                peak_val = float(item[1])
                break
        
        if peak_val is not None:
             mark_points_dtg.append({
                "coord": [peak_temp, peak_val],
                "name": f"{peak_temp:.0f} °C",
                "symbol": "triangle",
                "symbolSize": 8,
                "label": {
                    "show": True,
                    "formatter": f"{peak_temp:.0f} °C",
                    "position": "top",
                    "distance": 5,
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10,
                    "color": "#c0392b"
                }
            })

    if mark_points_weight:
        option["series"][0]["markPoint"] = {"data": mark_points_weight}
    if mark_points_dtg:
        option["series"][1]["markPoint"] = {"data": mark_points_dtg}

    return {
        "name": f"plot_{sheet_name.replace(' ', '_')}",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }

def main():
    xl = pd.ExcelFile(DATA_FILE)
    figures = []
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        fig = process_sheet(sheet_name, df)
        if fig:
            figures.append(fig)
            
    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
