import pandas as pd
import numpy as np
import json

def generate_tga_plot(df, sheet_name):
    # Identify columns based on standard TGA structure from preview
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
    
    # Ensure data is numeric and sorted by temperature
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y1_col] = pd.to_numeric(df[y1_col], errors='coerce')
    df[y2_col] = pd.to_numeric(df[y2_col], errors='coerce')
    df = df.dropna(subset=[x_col, y1_col, y2_col]).sort_values(by=x_col)
    
    temp = df[x_col].values.astype(float)
    weight = df[y1_col].values.astype(float)
    dtg = df[y2_col].values.astype(float)
    
    # Calculate Residue at ~800 C
    residue_val = None
    residue_x = None
    if len(temp) > 0:
        idx_res = np.argmin(np.abs(temp - 800.0))
        residue_val = float(weight[idx_res])
        residue_x = float(temp[idx_res])
        
    # Calculate Peak DTG above 150 C
    peak_temp = None
    peak_dtg_val = None
    mask_peak = temp > 150.0
    if np.any(mask_peak):
        dtg_masked = dtg[mask_peak]
        temp_masked = temp[mask_peak]
        # Find min value (most negative) which corresponds to max mass loss rate
        min_idx = np.argmin(dtg_masked)
        peak_temp = float(temp_masked[min_idx])
        peak_dtg_val = float(dtg_masked[min_idx])
        
    # Prepare series data
    # Weight series (left axis)
    weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    
    # DTG series (right axis, multiplied by -1 so peaks point up)
    dtg_data = [[float(t), float(-d)] for t, d in zip(temp, dtg)]
    
    # Markers for annotations
    mark_point_weight = []
    if residue_x is not None and residue_val is not None:
        mark_point_weight.append({
            "coord": [residue_x, residue_val],
            "value": f"Residue {residue_val:.1f}%",
            "symbol": "circle",
            "symbolSize": 6,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": f"Residue {residue_val:.1f}%",
                "position": "top",
                "fontSize": 9,
                "color": "#1f4e9c"
            }
        })
        
    mark_point_dtg = []
    if peak_temp is not None and peak_dtg_val is not None:
        # Note: On the chart, y2 is inverted (-dtg). So the peak position on chart is -peak_dtg_val
        mark_point_dtg.append({
            "coord": [peak_temp, -peak_dtg_val],
            "value": f"{peak_temp:.0f} °C",
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "fontSize": 9,
                "color": "#c0392b"
            }
        })

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
            "textStyle": {
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
            "data": ["Weight (%)", "DTG (%/°C)"],
            "top": 10,
            "right": 10,
            "orient": "vertical",
            "textStyle": {
                "fontSize": 9
            }
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": {
            "name": "Temperature (°C)",
            "type": "value",
            "min": 30,
            "max": 900,
            "splitLine": {
                "show": False
            },
            "axisLabel": {
                "fontSize": 10
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "type": "value",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#1f4e9c"
                    }
                },
                "axisLabel": {
                    "fontSize": 10,
                    "color": "#1f4e9c"
                },
                "splitLine": {
                    "show": False
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "value",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#c0392b"
                    }
                },
                "axisLabel": {
                    "fontSize": 10,
                    "color": "#c0392b"
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
                "data": weight_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 1.5
                },
                "markPoint": {
                    "data": mark_point_weight
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 1.5
                },
                "markPoint": {
                    "data": mark_point_dtg
                }
            }
        ]
    }

    return {
        "name": sheet_name.replace(" ", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    xl = pd.ExcelFile(file_path)
    figures = []
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        fig = generate_tga_plot(df, sheet_name)
        figures.append(fig)
        
    result = {"figures": figures}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
