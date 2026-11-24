import pandas as pd
import numpy as np
import json

def main():
    # 1. Load Data
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
    df = pd.read_csv(file_path)
    
    # Identify columns based on the preview
    # Time (min), Temperature (°C), Weight (%), Deriv. Weight (%/°C), Heat Flow (W/g)
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    dtg_col = "Deriv. Weight (%/°C)"
    
    # Extract data arrays
    temps = df[temp_col].values
    weights = df[weight_col].values
    dtgs = df[dtg_col].values
    
    # Calculate DTG peak for annotation (highest peak above 150°C)
    # Note: DTG is negative during mass loss, so we look for the minimum value (most negative) 
    # but the prompt says "multiplied by -1 so its peaks point up". 
    # So in the plot, positive values are peaks. We find the max of (-DTG) where Temp > 150.
    
    mask_150 = temps > 150
    if np.any(mask_150):
        dtg_negated = -dtgs[mask_150]
        temps_masked = temps[mask_150]
        
        idx_max_dtg = np.argmax(dtg_negated)
        peak_temp = temps_masked[idx_max_dtg]
        peak_val_display = dtg_negated[idx_max_dtg] # This is the height on the y2 axis (which is -DTG)
    else:
        peak_temp = None
        peak_val_display = None
        
    # Calculate Residue at ~800°C
    mask_800 = (temps >= 790) & (temps <= 810)
    if not np.any(mask_800):
         # Fallback to closest point to 800 if range not found
        idx_closest = np.argmin(np.abs(temps - 800))
        residue_weight = weights[idx_closest]
        residue_temp = temps[idx_closest]
    else:
        # Average or pick one? Usually pick the one closest to 800 within range or just the value at 800.
        # Let's take the average of points near 800 or the single closest.
        # Standard practice: value at the measured point nearest 800 °C.
        idx_closest_in_range = np.argmin(np.abs(temps[mask_800] - 800))
        residue_weight = weights[mask_800][idx_closest_in_range]
        residue_temp = temps[mask_800][idx_closest_in_range]

    # Prepare Series Data
    # Plot 1: Weight (%) vs Temperature
    series_weight_data = [[t, w] for t, w in zip(temps, weights)]
    
    # Plot 2: DTG (-DTG) vs Temperature
    # Prompt: "DTG ... multiplied by -1 so its peaks point up"
    series_dtg_data = [[t, -d] for t, d in zip(temps, dtgs)]
    
    # Markers for annotations
    markers_weight = []
    markers_dtg = []
    
    if residue_weight is not None and residue_temp is not None:
        markers_weight.append({
            "coord": [residue_temp, residue_weight],
            "value": f"Residue {residue_weight:.1f}%",
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{b}",
                "fontSize": 12,
                "color": "#333"
            }
        })
        
    if peak_temp is not None and peak_val_display is not None:
        markers_dtg.append({
            "coord": [peak_temp, peak_val_display],
            "value": f"{peak_temp:.0f} °C",
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{b}",
                "fontSize": 12,
                "color": "#333"
            }
        })

    # Common X Axis Configuration
    x_axis_config = {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": False},
        "axisTick": {"show": True}
    }

    # Option 1: Weight Plot
    option_weight = {
        "title": {
            "text": "caox - Weight (%)",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "grid": {
            "left": "10%",
            "right": "5%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": x_axis_config,
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": series_weight_data,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "markPoint": {
                    "data": markers_weight
                }
            }
        ]
    }

    # Option 2: DTG Plot
    option_dtg = {
        "title": {
            "text": "caox - DTG (%/°C)",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "grid": {
            "left": "10%",
            "right": "5%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": x_axis_config,
        "yAxis": {
            "type": "value",
            "name": "DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        "series": [
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": series_dtg_data,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "markPoint": {
                    "data": markers_dtg
                }
            }
        ]
    }

    result = {
        "figures": [
            {
                "name": "plot_weight",
                "option": option_weight,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            },
            {
                "name": "plot_dtg",
                "option": option_dtg,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
