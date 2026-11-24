import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def find_nearest_value(temp_arr, weight_arr, target_temp):
    """Find the weight value at the temperature closest to target_temp."""
    if len(temp_arr) == 0:
        return None, None
    idx = np.argmin(np.abs(temp_arr - target_temp))
    return float(temp_arr[idx]), float(weight_arr[idx])

def find_peak_info(temp_arr, dtg_arr, min_temp=150.0):
    """Find the temperature of the highest DTG peak above min_temp.
       Since DTG is negative during mass loss, we look for the most negative value (lowest point),
       which corresponds to the highest magnitude of mass loss rate.
       The prompt says 'multiplied by -1 so its peaks point up', implying we plot -DTG.
       So we look for the maximum of (-DTG) or minimum of DTG in the range > 150C.
    """
    mask = temp_arr > min_temp
    if not np.any(mask):
        return None, None
    
    t_masked = temp_arr[mask]
    dtg_masked = dtg_arr[mask]
    
    # We want the peak of the plotted curve, which is -DTG.
    # Max of (-DTG) is Min of DTG.
    idx_min_dtg = np.argmin(dtg_masked)
    peak_temp = float(t_masked[idx_min_dtg])
    peak_val_plotted = float(-dtg_masked[idx_min_dtg]) # Value on the y2 axis
    
    return peak_temp, peak_val_plotted

def generate_tga_option(df, sheet_name):
    # Extract columns based on standard TGA structure identified in preview
    # x = Temperature, y1 = Weight(%), y2 = D.W(%/C)
    
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    # Ensure data exists
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        return None
        
    temps = df[temp_col].values
    weights = df[weight_col].values
    dtgs = df[dtg_col].values
    
    # Prepare series data
    # Series 1: Weight (%) -> Left Y Axis
    # ECharts expects [[x, y], ...]
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # Series 2: DTG (%/C) * -1 -> Right Y Axis
    # Plotting -DTG makes peaks point up
    dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
    
    # Calculate Residue Label Info (nearest to 800 C)
    res_temp, res_weight = find_nearest_value(temps, weights, 800.0)
    residue_label_text = f"Residue {res_weight:.1f}%" if res_weight is not None else ""
    
    # Calculate Peak Label Info (highest DTG peak > 150 C)
    peak_temp, peak_val_plotted = find_peak_info(temps, dtgs, min_temp=150.0)
    peak_label_text = f"{peak_temp:.0f} °C" if peak_temp is not None else ""
    
    # Determine Axis Ranges dynamically to ensure good visibility
    # Y1 (Weight): usually 0-100 or slightly wider
    y1_min = max(0.0, float(np.min(weights)) - 5.0)
    y1_max = float(np.max(weights)) + 5.0
    
    # Y2 (DTG * -1): Find range of plotted values
    plotted_dtg_vals = [-float(d) for d in dtgs]
    y2_min = float(np.min(plotted_dtg_vals)) - 0.1
    y2_max = float(np.max(plotted_dtg_vals)) + 0.1
    # Ensure 0 is included and reasonable padding
    if y2_min > 0: y2_min = -0.1
    if y2_max < 0: y2_max = 0.1
    
    # X Range
    x_min = float(np.min(temps))
    x_max = float(np.max(temps))
    
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": "3%",
            "textStyle": {
                "fontSize": 14,
                "fontWeight": "bold",
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "show": False  # User requested to remove legend
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": x_min,
            "max": x_max,
            "splitLine": {
                "show": True,  # Grid on
                "lineStyle": {
                    "color": "#ccc",
                    "type": "dashed"
                }
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#666"
                }
            },
            "axisTick": {
                "show": True
            },
            "axisLabel": {
                "fontSize": 10,
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": y1_min,
                "max": y1_max,
                "position": "left",
                "splitLine": {
                    "show": True,  # Grid on
                    "lineStyle": {
                        "color": "#ccc",
                        "type": "dashed"
                    }
                },
                "axisLine": {
                    "lineStyle": {
                        "color": "#666"
                    }
                },
                "axisTick": {
                    "show": True
                },
                "axisLabel": {
                    "fontSize": 10,
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            {
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": y2_min,
                "max": y2_max,
                "position": "right",
                "splitLine": {
                    "show": False  # Usually secondary axis doesn't show grid lines to avoid clutter, but user said "격자 켜줘". 
                                   # Typically grid refers to the main background grid. I will keep right axis splitLine off for clarity unless strictly interpreted as ALL grids.
                                   # Standard practice: one set of grid lines. Left axis controls vertical/horizontal grid? No, xAxis controls vertical, yAxis controls horizontal.
                                   # If both Y axes have splitLine=True, they might overlap or conflict if scales differ significantly in position logic. 
                                   # However, ECharts handles this. To be safe and clean, I'll enable it for left only, or both if desired. 
                                   # Let's enable for left axis primarily.
                },
                "axisLine": {
                    "lineStyle": {
                        "color": "#666"
                    }
                },
                "axisTick": {
                    "show": True
                },
                "axisLabel": {
                    "fontSize": 10,
                    "fontFamily": "Noto Sans CJK KR"
                }
            }
        ],
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "data": weight_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [res_temp, res_weight],
                            "label": {
                                "show": True,
                                "formatter": residue_label_text,
                                "position": "top",
                                "fontSize": 10,
                                "color": "#1f4e9c",
                                "fontFamily": "Noto Sans CJK KR"
                            },
                            "symbolSize": 6,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                } if res_weight is not None else None
            },
            {
                "name": "DTG",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [peak_temp, peak_val_plotted],
                            "label": {
                                "show": True,
                                "formatter": peak_label_text,
                                "position": "top",
                                "fontSize": 10,
                                "color": "#c0392b",
                                "fontFamily": "Noto Sans CJK KR"
                            },
                            "symbolSize": 6,
                            "itemStyle": {
                                "color": "#c0392b"
                            }
                        }
                    ]
                } if peak_temp is not None else None
            }
        ]
    }
    
    # Clean up None markPoints if any
    for s in option["series"]:
        if "markPoint" in s and s["markPoint"] is None:
            del s["markPoint"]
            
    return option

def main():
    figures = []
    xls = pd.ExcelFile(DATA_FILE)
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Basic cleaning: drop rows with NaN in critical columns
        required_cols = ['Temperature', 'Weight(%)', 'D.W(%/C)']
        if all(c in df.columns for c in required_cols):
            df_clean = df.dropna(subset=required_cols)
            
            if not df_clean.empty:
                opt = generate_tga_option(df_clean, sheet_name)
                if opt:
                    fig_entry = {
                        "name": sheet_name.replace(" ", "_"),
                        "option": opt,
                        "width": 614,
                        "height": 442,
                        "dpi": 300,
                        "formats": ["png"]
                    }
                    figures.append(fig_entry)
                    
    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
