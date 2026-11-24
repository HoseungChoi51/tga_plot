import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def make_tga_option(df, sheet_name):
    temp = df['Temperature (°C)'].values
    weight = df['Weight (%)'].values
    dtg = df['Deriv. Weight (%/°C)'].values
    
    # Find residue at 800 °C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    
    # Find peak DTG above 150 °C (highest magnitude, i.e., most negative)
    mask_above_150 = temp > 150
    if np.any(mask_above_150):
        dtg_masked = dtg[mask_above_150]
        temp_masked = temp[mask_above_150]
        min_dtg_idx = np.argmin(dtg_masked)
        peak_temp = temp_masked[min_dtg_idx]
        peak_dtg_val = dtg_masked[min_dtg_idx]
    else:
        peak_temp = None
        peak_dtg_val = None

    # Prepare series data for TGA line (y1)
    tga_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    
    # Prepare series data for DTG line (y2), multiplied by -1
    dtg_data = [[float(t), float(-d)] for t, d in zip(temp, dtg)]
    
    # Determine axis ranges
    x_min = 30
    x_max = 900
    y1_min = 0
    y1_max = 100
    
    # For y2, we want to show the inverted DTG peaks pointing up
    # The original dtg is negative during mass loss, so -dtg is positive
    max_inv_dtg = np.max(-dtg) if len(dtg) > 0 else 0
    min_inv_dtg = np.min(-dtg) if len(dtg) > 0 else 0
    y2_min = min(min_inv_dtg, 0)
    y2_max = max(max_inv_dtg, 0)
    
    # Add some padding
    if y2_max == y2_min:
        y2_max = y2_min + 1
    y2_range = y2_max - y2_min
    y2_min -= y2_range * 0.1
    y2_max += y2_range * 0.1
    
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
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": {
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": x_min,
            "max": x_max,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": y1_min,
                "max": y1_max,
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {"lineStyle": {"color": "#eee"}}
            },
            {
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": round(y2_min, 2),
                "max": round(y2_max, 2),
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": tga_data,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(temp[idx_800]), float(residue_val)],
                            "symbolSize": 8,
                            "itemStyle": {"color": "#1f4e9c"},
                            "label": {
                                "show": True,
                                "formatter": f"Residue {residue_val:.1f}%",
                                "position": "top",
                                "fontFamily": "Noto Sans CJK KR",
                                "fontSize": 9,
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                },
                "markLine": {
                    "silent": True,
                    "symbol": "none",
                    "lineStyle": {"type": "dashed", "color": "#666"},
                    "label": {
                        "show": True,
                        "formatter": "50%",
                        "position": "start",
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 9
                    },
                    "data": [
                        {"yAxis": 50}
                    ]
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": True,
                "symbol": "none",
                "lineStyle": {"color": "#c0392b", "width": 2},
                "markPoint": {
                    "data": []
                }
            }
        ],
        "graphic": [
            {
                "type": "text",
                "right": 10,
                "top": 10,
                "style": {
                    "text": "공기, 10 °C/min",
                    "font": "10px Noto Sans CJK KR",
                    "fill": "#333"
                }
            }
        ]
    }
    
    # Add peak marker if found
    if peak_temp is not None:
        # We need to find the corresponding -dtg value at peak_temp
        # Since we already have dtg_data, let's just use the index from masked array logic or re-search
        # Actually easier: search in original arrays
        idx_peak = np.argmin(dtg) # This finds the most negative DTG overall, but we filtered >150 earlier
        # Let's redo properly for the markpoint on the DTG curve (which is plotted as -dtg)
        # The peak of interest is where dtg is minimum (most negative). On the plot, this is maximum of -dtg.
        
        # Re-find with constraint
        valid_indices = np.where(temp > 150)[0]
        if len(valid_indices) > 0:
            sub_dtg = dtg[valid_indices]
            sub_temp = temp[valid_indices]
            local_min_idx = np.argmin(sub_dtg)
            global_idx = valid_indices[local_min_idx]
            
            peak_t = temp[global_idx]
            peak_d_val = -dtg[global_idx] # Value on the right axis
            
            option["series"][1]["markPoint"]["data"].append({
                "coord": [float(peak_t), float(peak_d_val)],
                "symbolSize": 8,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{peak_t:.0f} °C",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 9,
                    "color": "#c0392b"
                }
            })

    return option

figures = []
xl = pd.ExcelFile(DATA_FILE)
for sheet_name in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet_name)
    opt = make_tga_option(df, sheet_name)
    figures.append({
        "name": sheet_name.replace(" ", "_"),
        "option": opt,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

print(json.dumps({"figures": figures}))
