import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def get_data_for_sheet(sheet_name):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Identify columns based on standard TGA structure or names
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        if 'temperature' in str(col).lower():
            temp_col = col
        elif 'weight (%)' in str(col).lower() or 'weight' == str(col).lower():
            # Be careful not to pick derivative weight
            if 'deriv' not in str(col).lower() and 'dtg' not in str(col).lower():
                weight_col = col
        elif 'deriv' in str(col).lower() or 'dtg' in str(col).lower():
            dtg_col = col
            
    # Fallback to positional if names are ambiguous (A=Time, B=Temp, C=Weight, D=DTG)
    if temp_col is None: temp_col = df.columns[1]
    if weight_col is None: weight_col = df.columns[2]
    if dtg_col is None: dtg_col = df.columns[3]

    temps_c = df[temp_col].values
    weights = df[weight_col].values
    dtgs = df[dtg_col].values
    
    # Convert Celsius to Kelvin
    temps_k = temps_c + 273.15
    
    return temps_k, weights, dtgs

def calculate_labels(temps, weights, dtgs):
    # Find residue at nearest 800°C -> converted to K is 1073.15 K
    target_temp_k = 800 + 273.15
    idx_residue = np.argmin(np.abs(temps - target_temp_k))
    residue_val = weights[idx_residue]
    residue_temp = temps[idx_residue]
    
    # Find DTG peak above 150°C (423.15 K)
    mask = temps > (150 + 273.15)
    if np.any(mask):
        # DTG is negative during mass loss, so we look for the minimum value (most negative)
        # which corresponds to the highest rate of loss.
        dtg_masked = dtgs[mask]
        temps_masked = temps[mask]
        
        # Find index of minimum DTG (peak of degradation)
        min_dtg_idx_local = np.argmin(dtg_masked)
        peak_temp = temps_masked[min_dtg_idx_local]
        peak_weight = weights[mask][min_dtg_idx_local]
    else:
        peak_temp = None
        peak_weight = None
        
    return {
        "residue_temp": float(residue_temp),
        "residue_weight": float(residue_val),
        "peak_temp": float(peak_temp) if peak_temp is not None else None,
        "peak_weight": float(peak_weight) if peak_weight is not None else None
    }

def create_tga_option(sheet_name, temps, weights, dtgs, labels):
    # Prepare data arrays
    # ECharts expects [x, y] pairs for line series usually, or separate x/y axes with data objects.
    # Using dataset approach or simple array mapping.
    
    # For Weight (y1): [Temp(K), Weight(%)]
    data_weight = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    # For DTG (y2): [Temp(K), -DTG] to make peaks point up
    data_dtg = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
    
    # Axis ranges
    x_min = min(temps)
    x_max = max(temps)
    
    y1_min = 0
    y1_max = 100
    
    # Calculate Y2 range for DTG (already negated, so positive peaks)
    dtg_vals_negated = [-d for d in dtgs]
    y2_min = min(dtg_vals_negated)
    y2_max = max(dtg_vals_negated)
    # Add some padding
    y2_range = y2_max - y2_min
    y2_min -= y2_range * 0.1
    y2_max += y2_range * 0.1

    option = {
        "title": {
            "text": f"{sheet_name} TGA (Kelvin)",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
            }
        },
        "tooltip": {
            "trigger": "axis",
            "formatter": "{a}: {c}<br/>Temperature: {b} K"
        },
        "legend": {
            "data": ["Weight (%)", "-DTG (%/°C)"],
            "top": 30,
            "left": "center",
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
            "name": "Temperature (K)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": x_min,
            "max": x_max,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "min": y1_min,
                "max": y1_max,
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed"
                    }
                }
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "position": "right",
                "min": y2_min,
                "max": y2_max,
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
                "data": data_weight,
                "smooth": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "symbol": "none",
                "markPoint": {
                    "data": []
                }
            },
            {
                "name": "-DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data_dtg,
                "smooth": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#c0392b"
                },
                "symbol": "none",
                "markPoint": {
                    "data": []
                }
            }
        ]
    }
    
    # Add MarkPoints for Residue and Peak
    mark_points = []
    
    # Residue Marker
    if labels["residue_temp"] is not None:
        mark_points.append({
            "coord": [labels["residue_temp"], labels["residue_weight"]],
            "value": f"Residue {labels['residue_weight']:.1f}%",
            "symbolSize": 8,
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}",
                "color": "#1f4e9c",
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "itemStyle": {
                "color": "#1f4e9c"
            }
        })
        
    # Peak Marker
    if labels["peak_temp"] is not None:
        # The peak temperature label should be placed near the DTG curve peak
        # But visually it's often good to put it slightly offset or just label the coordinate
        # We use the second series (index 1) for this marker logically, but markPoint can be attached to any series.
        # Let's attach it to the DTG series for clarity in legend association if needed, 
        # but here we just add to the first series or a dummy one? 
        # ECharts markPoint works per series. Let's add to the DTG series.
        pass 

    # Re-construct series to include markPoints properly
    
    # Update Weight Series with Residue MarkPoint
    option["series"][0]["markPoint"] = {
        "data": [
            {
                "coord": [labels["residue_temp"], labels["residue_weight"]],
                "value": f"Residue {labels['residue_weight']:.1f}%",
                "symbolSize": 8,
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{c}",
                    "color": "#1f4e9c",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                }
            }
        ]
    }
    
    # Update DTG Series with Peak MarkPoint
    if labels["peak_temp"] is not None:
        # Note: The y-value for the marker on the DTG plot needs to be the -DTG value at that temp
        # We need to find the exact -DTG value corresponding to peak_temp
        # Since peak_temp was derived from the masked array, we might have floating point mismatches.
        # Safer to find index in original array closest to peak_temp
        
        idx_peak = np.argmin(np.abs(temps - labels["peak_temp"]))
        peak_y_val = -dtgs[idx_peak]
        
        option["series"][1]["markPoint"] = {
            "data": [
                {
                    "coord": [labels["peak_temp"], peak_y_val],
                    "value": f"{labels['peak_temp']:.0f} K",
                    "symbolSize": 8,
                    "label": {
                        "show": True,
                        "position": "top",
                        "formatter": "{c}",
                        "color": "#c0392b",
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 10
                    },
                    "itemStyle": {
                        "color": "#c0392b"
                    }
                }
            ]
        }

    return option

# Process PE Sheet
sheet_name = "PE"
temps, weights, dtgs = get_data_for_sheet(sheet_name)
labels = calculate_labels(temps, weights, dtgs)
option = create_tga_option(sheet_name, temps, weights, dtgs, labels)

output = {
    "figures": [
        {
            "name": "plot_PE_Kelvin",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
