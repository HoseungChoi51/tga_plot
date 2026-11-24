import json
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def find_column(df, candidates):
    for col in df.columns:
        for cand in candidates:
            if cand.lower() in str(col).lower():
                return col
    return None

def get_tga_data(df):
    temp_col = find_column(df, ["temperature", "temp"])
    weight_col = find_column(df, ["weight (%)", "weight%"])
    dtg_col = find_column(df, ["deriv", "dtg"])
    
    if not all([temp_col, weight_col, dtg_col]):
        # Fallback to standard positions if names don't match well but structure is known
        cols = list(df.columns)
        if len(cols) >= 4:
            temp_col = cols[1]
            weight_col = cols[2]
            dtg_col = cols[3]
            
    return df[temp_col].values, df[weight_col].values, df[dtg_col].values

def make_plot_option(temp, weight, dtg, sheet_name):
    # Filter valid data
    mask = ~(np.isnan(temp) | np.isnan(weight) | np.isnan(dtg))
    t = temp[mask]
    w = weight[mask]
    d = dtg[mask]
    
    # Sort by temperature ascending for processing
    idx = np.argsort(t)
    t_sorted = t[idx]
    w_sorted = w[idx]
    d_sorted = d[idx]
    
    # Calculate Residue at ~800°C
    # Find point closest to 800
    idx_800 = np.argmin(np.abs(t_sorted - 800))
    residue_val = w_sorted[idx_800]
    residue_temp = t_sorted[idx_800]
    
    # Calculate Peak DTG above 150°C
    # DTG is negative during mass loss. We want the highest magnitude (most negative), 
    # which corresponds to the lowest value in raw DTG.
    # However, the prompt says "multiplied by -1 so its peaks point up".
    # So we look for the minimum of raw DTG (which becomes maximum after * -1) where T > 150.
    
    mask_peak = t_sorted > 150
    if np.any(mask_peak):
        t_peak_region = t_sorted[mask_peak]
        d_peak_region = d_sorted[mask_peak]
        
        # Find index of minimum raw DTG (maximum loss rate)
        min_dtg_idx_local = np.argmin(d_peak_region)
        peak_temp = t_peak_region[min_dtg_idx_local]
        peak_dtg_raw = d_peak_region[min_dtg_idx_local]
    else:
        peak_temp = 0
        peak_dtg_raw = 0

    # Prepare data arrays for ECharts
    # Data format: [x, y] pairs
    # Note: The user requested x-axis reversed (high temp on left).
    # In ECharts, we can set xAxis inverse: true.
    
    data_weight = [[float(ti), float(wi)] for ti, wi in zip(t_sorted, w_sorted)]
    # For DTG, we multiply by -1 to make peaks point up
    data_dtg = [[float(ti), float(-di)] for ti, di in zip(t_sorted, d_sorted)]
    
    # Labels configuration
    labels = []
    
    # Residue Label
    labels.append({
        "type": "scatter",
        "name": "Residue Marker",
        "data": [[float(residue_temp), float(residue_val)]],
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_val:.1f}%",
            "position": "top",
            "distance": 5,
            "fontSize": 10,
            "fontFamily": "Noto Sans CJK KR",
            "color": "#1f4e9c"
        },
        "z": 10
    })
    
    # Peak Label
    if peak_temp > 0:
        labels.append({
            "type": "scatter",
            "name": "Peak Marker",
            "data": [[float(peak_temp), float(-peak_dtg_raw)]],
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{int(peak_temp)} °C",
                "position": "top",
                "distance": 5,
                "fontSize": 10,
                "fontFamily": "Noto Sans CJK KR",
                "color": "#c0392b"
            },
            "z": 10
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
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": ["Weight (%)", "DTG (%/°C)"],
            "left": "left",
            "orient": "vertical",
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
            "nameGap": 30,
            "inverse": True,  # Reverse X axis: High Temp Left, Low Temp Right
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#eee"
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#eee"
                    }
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
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
                "data": data_weight,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#1f4e9c"
                },
                "yAxisIndex": 0,
                "z": 1
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": data_dtg,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#c0392b"
                },
                "yAxisIndex": 1,
                "z": 1
            }
        ] + labels
    }
    
    return option

def main():
    xls = pd.ExcelFile(DATA_FILE)
    figures = []
    
    # Only process 'Raw' sheet as requested
    sheet_names = ["Raw"]
    
    for sheet in sheet_names:
        if sheet not in xls.sheet_names:
            continue
            
        df = pd.read_excel(xls, sheet_name=sheet, header=0)
        temp, weight, dtg = get_tga_data(df)
        
        if len(temp) == 0:
            continue
            
        option = make_plot_option(temp, weight, dtg, sheet)
        
        fig_entry = {
            "name": f"plot_{sheet.replace(' ', '_')}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(fig_entry)
        
    result = {"figures": figures}
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
