import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def find_column(df, keywords):
    for col in df.columns:
        if any(k.lower() in str(col).lower() for k in keywords):
            return col
    return None

def process_sheet(df, sheet_name):
    # Identify columns
    temp_col = find_column(df, ['temperature', 'temp'])
    weight_col = find_column(df, ['weight', 'wt'])
    dtg_col = find_column(df, ['d.w', 'dtg', 'derivative', 'dw'])
    
    if not all([temp_col, weight_col, dtg_col]):
        return None
    
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2_raw = df[dtg_col].values
    
    # Filter valid data
    mask = ~np.isnan(x) & ~np.isnan(y1) & ~np.isnan(y2_raw)
    x = x[mask]
    y1 = y1[mask]
    y2_raw = y2_raw[mask]
    
    # Invert DTG so peaks point up
    y2 = -y2_raw
    
    # Calculate Residue at 800C
    idx_800 = np.argmin(np.abs(x - 800))
    residue_val = y1[idx_800]
    residue_temp = x[idx_800]
    
    # Calculate Peak above 150C
    mask_peak = x > 150
    if np.any(mask_peak):
        y2_filtered = y2[mask_peak]
        x_filtered = x[mask_peak]
        peak_idx_local = np.argmax(y2_filtered)
        peak_temp = x_filtered[peak_idx_local]
        peak_val = y2_filtered[peak_idx_local]
    else:
        peak_temp = None
        peak_val = None

    # Prepare series data
    data_tga = [[float(a), float(b)] for a, b in zip(x, y1)]
    data_dtg = [[float(a), float(b)] for a, b in zip(x, y2)]
    
    # Markers for labels
    markers = []
    if residue_temp is not None and residue_val is not None:
        markers.append({
            "coord": [float(residue_temp), float(residue_val)],
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": f"Residue {residue_val:.1f}%",
                "position": "top",
                "fontSize": 12,
                "color": "#1f4e9c"
            }
        })
        
    if peak_temp is not None and peak_val is not None:
        markers.append({
            "coord": [float(peak_temp), float(peak_val)],
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "fontSize": 12,
                "color": "#c0392b"
            }
        })

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
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
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "name": "무게 (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 14
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": False
                }
            },
            {
                "name": "미분 무게 (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 14
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
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
                "data": data_tga,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [m["coord"] for m in markers if m["itemStyle"]["color"] == "#1f4e9c"]
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data_dtg,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": [m["coord"] for m in markers if m["itemStyle"]["color"] == "#c0392b"]
                }
            }
        ]
    }
    
    # Add markPoints properly to series if needed, or use scatter overlay. 
    # ECharts markPoint on line series works well.
    
    # Re-construct markPoint data structure correctly for each series
    mp_tga = []
    mp_dtg = []
    
    for m in markers:
        pt_data = {
            "coord": m["coord"],
            "value": m["label"]["formatter"],
            "symbol": m["symbol"],
            "symbolSize": m["symbolSize"],
            "itemStyle": m["itemStyle"],
            "label": m["label"]
        }
        if m["itemStyle"]["color"] == "#1f4e9c":
            mp_tga.append(pt_data)
        elif m["itemStyle"]["color"] == "#c0392b":
            mp_dtg.append(pt_data)
            
    option["series"][0]["markPoint"] = {"data": mp_tga}
    option["series"][1]["markPoint"] = {"data": mp_dtg}

    return {
        "name": sheet_name.replace(" ", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }

def main():
    xl_file = pd.ExcelFile(DATA_FILE)
    figures = []
    
    for sheet_name in xl_file.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
        fig_opt = process_sheet(df, sheet_name)
        if fig_opt:
            figures.append(fig_opt)
            
    result = {"figures": figures}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
