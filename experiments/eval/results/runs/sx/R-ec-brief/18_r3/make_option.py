import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def find_nearest(values, target):
    """Find the index of the value nearest to target."""
    return int(np.argmin(np.abs(values - target)))

def process_sheet(df, sheet_name):
    # Identify columns based on standard TGA structure or guess
    cols = df.columns.tolist()
    
    # Heuristic to find columns if names vary slightly
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl:
            temp_col = c
        elif 'weight' in cl and '%' in cl:
            weight_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            dtg_col = c
            
    # Fallback to positional if heuristic fails (based on preview)
    if temp_col is None: temp_col = cols[1]
    if weight_col is None: weight_col = cols[2]
    if dtg_col is None: dtg_col = cols[3]

    temps = df[temp_col].values
    weights = df[weight_col].values
    dtgs = df[dtg_col].values
    
    # Clean data: remove NaNs
    mask = ~(np.isnan(temps) | np.isnan(weights) | np.isnan(dtgs))
    temps = temps[mask]
    weights = weights[mask]
    dtgs = dtgs[mask]

    # Prepare data for ECharts series
    # Weight line (y1)
    weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # DTG line (y2), multiplied by -1 so peaks point up
    dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
    
    # Calculate Residue at 800°C
    # If max temp < 800, use last point? The prompt says "nearest 800 C".
    idx_res = find_nearest(temps, 800.0)
    res_temp = temps[idx_res]
    res_weight = weights[idx_res]
    residue_label = f"Residue {res_weight:.1f}%"
    
    # Find Peak Temperature (highest DTG peak above 150 C)
    # We look at original DTGs (negative values mean mass loss). 
    # The peak corresponds to the most negative DTG value.
    # But we plotted -DTG. So the highest positive value in -DTG is the peak.
    # Condition: Temp > 150
    valid_peaks_mask = temps > 150
    if not np.any(valid_peaks_mask):
        peak_temp = None
        peak_val = None
    else:
        # Filtered arrays
        v_temps = temps[valid_peaks_mask]
        v_dtgs = dtgs[valid_peaks_mask] # Original negative values
        
        # Most negative DTG = biggest drop
        min_dtg_idx = np.argmin(v_dtgs)
        peak_temp = v_temps[min_dtg_idx]
        peak_val = -v_dtgs[min_dtg_idx] # Value on the inverted plot
        
    # Construct Option
    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
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
            "data": ["Weight (%)", "DTG"],
            "orient": "vertical",
            "left": "left",
            "top": "middle"
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
            "min": 0,
            "max": 950, # Adjust based on data max, but usually fixed range is good
            "splitLine": {
                "show": False
            },
            "axisTick": {
                "interval": 100,
                "alignWithLabel": True
            },
            "axisLabel": {
                "formatter": "{value}"
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "type": "value",
                "position": "left",
                "splitLine": {
                    "lineStyle": {
                        "color": "#ccc",
                        "type": "dashed"
                    }
                },
                "axisLabel": {
                    "formatter": "{value} %"
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "value",
                "position": "right",
                "min": -0.05,
                "max": 1.2,
                "splitLine": {
                    "show": False
                },
                "axisLabel": {
                    "formatter": "{value}"
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
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [float(res_temp), float(res_weight)],
                            "name": "Residue",
                            "symbolSize": 8,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            },
                            "label": {
                                "show": True,
                                "formatter": residue_label,
                                "position": "top",
                                "distance": 5,
                                "fontSize": 10
                            }
                        }
                    ]
                }
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
                    "data": []
                }
            }
        ]
    }
    
    # Add Peak Marker if found
    if peak_temp is not None:
        option["series"][1]["markPoint"]["data"].append({
            "coord": [float(peak_temp), float(peak_val)],
            "name": "Peak",
            "symbolSize": 8,
            "itemStyle": {
                "color": "#c0392b"
            },
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "distance": 5,
                "fontSize": 10
            }
        })

    return option

# Load Excel file
xls = pd.ExcelFile(DATA_FILE)
figures = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Basic cleaning: drop rows where key columns are missing
    # Assuming first row is header handled by read_excel default
    # Ensure numeric conversion
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            pass
            
    option = process_sheet(df, sheet_name)
    
    figures.append({
        "name": sheet_name.replace(" ", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

output = {"figures": figures}
print(json.dumps(output))
