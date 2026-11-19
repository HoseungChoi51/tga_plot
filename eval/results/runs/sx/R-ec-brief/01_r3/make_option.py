import pandas as pd
import numpy as np
import json

def get_korean_font():
    return "Noto Sans CJK KR"

def find_nearest_value(x_arr, y_arr, target_x):
    if len(x_arr) == 0:
        return None, None
    idx = np.argmin(np.abs(x_arr - target_x))
    return x_arr[idx], y_arr[idx]

def find_peak_info(x_arr, dtg_arr, min_temp=150.0):
    # Find the highest DTG peak (most negative value in original data, which becomes positive after * -1)
    # We look for the minimum value in dtg_arr that is below zero and where temp > min_temp
    mask = (x_arr >= min_temp) & (dtg_arr < 0)
    if not np.any(mask):
        return None, None
    
    filtered_dtg = dtg_arr[mask]
    filtered_x = x_arr[mask]
    
    # Peak is the most negative DTG value (lowest point on original curve, highest on inverted)
    peak_idx_local = np.argmin(filtered_dtg)
    peak_temp = filtered_x[peak_idx_local]
    peak_val = filtered_dtg[peak_idx_local]
    
    return peak_temp, peak_val

def create_tga_option(df, sheet_name):
    font_family = get_korean_font()
    
    # Extract columns based on standard TGA structure guessed from preview
    # B: Temperature, C: Weight(%), D: D.W(%/C)
    try:
        temps = df['Temperature'].values
        weights = df['Weight(%)'].values
        dtgs = df['D.W(%/C)'].values
    except KeyError:
        # Fallback if column names differ slightly, though preview suggests these are correct
        return None

    # Calculate Residue at 800°C
    res_temp, res_weight = find_nearest_value(temps, weights, 800.0)
    
    # Calculate DTG Peak above 150°C
    peak_temp, peak_dtg_val = find_peak_info(temps, dtgs, 150.0)
    
    # Prepare series data
    # Weight Series (Left Y)
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # DTG Series (Right Y, multiplied by -1 to make peaks point up)
    dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
    
    # Markers for labels
    markers = []
    
    if res_weight is not None:
        markers.append({
            "coord": [float(res_temp), float(res_weight)],
            "symbolSize": 6,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": f"Residue {res_weight:.1f}%",
                "position": "top",
                "fontSize": 12,
                "fontFamily": font_family,
                "color": "#333"
            }
        })
        
    if peak_temp is not None:
        # Note: The marker for the peak should be on the DTG curve (right axis).
        # The coordinate needs to match the transformed DTG value (-peak_dtg_val)
        # However, ECharts scatter/markPoint coordinates refer to the specific yAxisIndex of the series they belong to.
        # If we add it to the DTG series, coord is [temp, -peak_dtg_val].
        pass 

    option = {
        "backgroundColor": "#fff",
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontFamily": font_family,
                "fontSize": 16,
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
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {
                "fontFamily": font_family,
                "fontSize": 12
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
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "scale": False,
            "axisLine": {
                "lineStyle": {
                    "color": "#666"
                }
            },
            "axisTick": {
                "show": True,
                "alignWithLabel": True
            },
            "axisLabel": {
                "fontFamily": font_family,
                "fontSize": 10
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#1f4e9c"
                    }
                },
                "axisTick": {
                    "show": True
                },
                "axisLabel": {
                    "fontFamily": font_family,
                    "fontSize": 10,
                    "color": "#1f4e9c"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#eee"
                    }
                }
            },
            {
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#c0392b"
                    }
                },
                "axisTick": {
                    "show": True
                },
                "axisLabel": {
                    "fontFamily": font_family,
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
                "yAxisIndex": 0,
                "data": weight_data,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(res_temp), float(res_weight)],
                            "symbol": "circle",
                            "symbolSize": 6,
                            "itemStyle": {"color": "#1f4e9c"},
                            "label": {
                                "show": True,
                                "formatter": f"Residue {res_weight:.1f}%",
                                "position": "top",
                                "fontSize": 12,
                                "fontFamily": font_family,
                                "color": "#333"
                            }
                        }
                    ] if res_weight is not None else []
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": False,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(peak_temp), float(-peak_dtg_val)],
                            "symbol": "triangle",
                            "symbolSize": 8,
                            "itemStyle": {"color": "#c0392b"},
                            "label": {
                                "show": True,
                                "formatter": f"{peak_temp:.0f} °C",
                                "position": "top",
                                "fontSize": 12,
                                "fontFamily": font_family,
                                "color": "#333"
                            }
                        }
                    ] if peak_temp is not None else []
                }
            }
        ]
    }
    
    return option

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
    
    # Read all sheets
    xls = pd.ExcelFile(file_path)
    figures = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Clean column names just in case
        df.columns = [str(c).strip() for c in df.columns]
        
        option = create_tga_option(df, sheet_name)
        
        if option:
            fig_entry = {
                "name": f"plot_{sheet_name.replace(' ', '_')}",
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
