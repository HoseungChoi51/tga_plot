import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

def find_nearest_value(temp_arr, weight_arr, target_temp):
    """Find the weight value at the temperature nearest to target_temp."""
    if len(temp_arr) == 0:
        return None, None
    idx = np.argmin(np.abs(temp_arr - target_temp))
    return temp_arr[idx], weight_arr[idx]

def find_dtg_peak(temp_arr, dtg_arr, min_temp=150.0):
    """Find the temperature and value of the highest DTG peak above min_temp."""
    # Filter for temperatures > min_temp
    mask = temp_arr > min_temp
    if not np.any(mask):
        return None, None
    
    filtered_temp = temp_arr[mask]
    filtered_dtg = dtg_arr[mask]
    
    # Find index of maximum absolute DTG (since we flip sign later, looking for most negative original is same as max positive flipped)
    # But usually "peak" in TGA context refers to the magnitude of mass loss rate. 
    # The prompt says "highest DTG peak... multiplied by -1 so its peaks point up".
    # So we look for the minimum value in the original DTG (most negative), which becomes the maximum when multiplied by -1.
    
    min_idx = np.argmin(filtered_dtg)
    peak_temp = filtered_temp[min_idx]
    peak_val_original = filtered_dtg[min_idx]
    
    return peak_temp, peak_val_original

def create_tga_option(df, sheet_name):
    temp = df['Temperature'].values
    weight = df['Weight(%)'].values
    dtg = df['D.W(%/C)'].values
    
    # Calculate residue at ~800 C
    res_temp, res_weight = find_nearest_value(temp, weight, 800.0)
    
    # Calculate DTG peak above 150 C
    peak_temp, peak_dtg_orig = find_dtg_peak(temp, dtg, 150.0)
    
    # Prepare data series
    # Series 1: Weight (%) on y1
    weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    
    # Series 2: DTG (-DTG) on y2
    # Multiply by -1 to make peaks point up
    dtg_data = [[float(t), float(-d)] for t, d in zip(temp, dtg)]
    
    # Determine axis ranges roughly to set reasonable defaults or let echarts auto-scale mostly
    # We will use type 'value' for axes
    
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "top",
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
            "data": ["Weight (%)", "-DTG (%/°C)"],
            "left": "left",
            "top": "middle",
            "orient": "vertical"
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%"
        },
        "xAxis": [
            {
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 30,
                "type": "value",
                "axisTick": {
                    "show": True,
                    "length": 6,
                    "lineStyle": {
                        "color": "#333"
                    }
                },
                "axisLabel": {
                    "fontSize": 9
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "left",
                "axisTick": {
                    "show": True,
                    "length": 6,
                    "lineStyle": {
                        "color": "#333"
                    }
                },
                "axisLabel": {
                    "fontSize": 9
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
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "axisTick": {
                    "show": True,
                    "length": 6,
                    "lineStyle": {
                        "color": "#333"
                    }
                },
                "axisLabel": {
                    "fontSize": 9
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
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "lineStyle": {
                    "width": 2,
                    "color": "#1f4e9c"
                },
                "symbol": "none",
                "markPoint": {}
            },
            {
                "name": "-DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "itemStyle": {
                    "color": "#c0392b"
                },
                "lineStyle": {
                    "width": 2,
                    "color": "#c0392b"
                },
                "symbol": "none",
                "markPoint": {}
            }
        ]
    }
    
    # Add markers for Residue and Peak if found
    mark_points_weight = []
    mark_points_dtg = []
    
    if res_weight is not None:
        # Marker on Weight curve
        mark_points_weight.append({
            "coord": [float(res_temp), float(res_weight)],
            "label": {
                "show": True,
                "formatter": f"Residue {res_weight:.1f}%",
                "position": "right",
                "fontSize": 10,
                "color": "#1f4e9c"
            },
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {
                "color": "#1f4e9c"
            }
        })
        
    if peak_temp is not None:
        # Marker on DTG curve (remember we plotted -DTG)
        # The value on the plot is -peak_dtg_orig
        plot_dtg_val = -peak_dtg_orig
        mark_points_dtg.append({
            "coord": [float(peak_temp), float(plot_dtg_val)],
            "label": {
                "show": True,
                "formatter": f"{int(peak_temp)} °C",
                "position": "top",
                "fontSize": 10,
                "color": "#c0392b"
            },
            "symbol": "triangle",
            "symbolSize": 8,
            "itemStyle": {
                "color": "#c0392b"
            }
        })
        
    if mark_points_weight:
        option["series"][0]["markPoint"] = {
            "data": mark_points_weight
        }
        
    if mark_points_dtg:
        option["series"][1]["markPoint"] = {
            "data": mark_points_dtg
        }

    return option

figures = []
xl_file = pd.ExcelFile(DATA_FILE)

for sheet_name in xl_file.sheet_names:
    df = pd.read_excel(xl_file, sheet_name=sheet_name)
    
    # Check required columns exist
    if 'Temperature' in df.columns and 'Weight(%)' in df.columns and 'D.W(%/C)' in df.columns:
        opt = create_tga_option(df, sheet_name)
        figures.append({
            "name": f"plot_{sheet_name.replace(' ', '_')}",
            "option": opt,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

output = {"figures": figures}
print(json.dumps(output, ensure_ascii=False))
