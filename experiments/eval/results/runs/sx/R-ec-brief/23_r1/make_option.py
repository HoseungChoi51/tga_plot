import pandas as pd
import numpy as np
import json

def parse_tga_file(filepath):
    # Read the file, skipping first 10 rows based on preview (data_start_row: 11)
    # Using header=None to handle raw data structure
    df = pd.read_csv(filepath, sep=r'\s+', header=None, skiprows=10, engine='python')
    
    # Drop rows with NaN if any parsing issues occurred at edges
    df.dropna(inplace=True)
    
    # Identify columns based on TGA guess from preview:
    # Col A (index 0): Time? (ignored for plot x-axis)
    # Col B (index 1): Temperature (x)
    # Col C (index 2): Weight % (y1)
    # Col D (index 3): DTG (y2)
    
    temp_col = 1
    weight_col = 2
    dtg_col = 3
    
    temps = df.iloc[:, temp_col].values
    weights = df.iloc[:, weight_col].values
    dtgs = df.iloc[:, dtg_col].values
    
    return temps, weights, dtgs

def find_nearest_value(arr, target):
    idx = (np.abs(arr - target)).argmin()
    return arr[idx], idx

def calculate_metrics(temps, weights, dtgs):
    # Residue at nearest 800 °C
    _, res_idx = find_nearest_value(temps, 800.0)
    residue_val = weights[res_idx]
    residue_temp = temps[res_idx]
    
    # Peak temperature of highest DTG peak above 150 °C
    # Filter for temp > 150
    mask = temps > 150
    if not np.any(mask):
        peak_temp = None
        peak_dtg = None
    else:
        filtered_temps = temps[mask]
        filtered_dtgs = dtgs[mask]
        
        # Find max absolute DTG (since DTG is negative during loss, we look for min value or max abs)
        # The prompt says "highest DTG peak", usually meaning the most negative value in raw DTG, 
        # which becomes the highest positive peak when multiplied by -1.
        # So we look for the minimum value in the original DTG column within the range.
        min_dtg_idx_local = np.argmin(filtered_dtgs)
        peak_temp = filtered_temps[min_dtg_idx_local]
        peak_dtg = filtered_dtgs[min_dtg_idx_local]
        
    return residue_val, residue_temp, peak_temp, peak_dtg

def main():
    filepath = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"
    
    try:
        temps, weights, dtgs = parse_tga_file(filepath)
        
        if len(temps) == 0:
            print(json.dumps({"figures": []}))
            return
            
        residue_val, residue_temp, peak_temp, peak_dtg = calculate_metrics(temps, weights, dtgs)
        
        # Prepare data for ECharts
        # Series 1: Weight (Left Y Axis)
        # Format: [temp, weight]
        weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
        
        # Series 2: DTG (Right Y Axis)
        # Multiply by -1 so peaks point up
        # Format: [temp, -dtg]
        dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]
        
        # Determine axis ranges for better visualization
        min_temp = float(np.min(temps))
        max_temp = float(np.max(temps))
        
        # Add some padding to axes
        y1_min = float(np.min(weights)) * 0.95
        y1_max = float(np.max(weights)) * 1.05
        
        # For DTG, since it's inverted, we want the visual peaks to be visible.
        # Original DTG min (most negative) becomes max positive.
        # Original DTG max (least negative/positive) becomes min/negative.
        dtg_vals_inv = [-d for d in dtgs]
        y2_min = float(np.min(dtg_vals_inv))
        y2_max = float(np.max(dtg_vals_inv))
        
        # Ensure y2 range covers 0 nicely if needed, but typically auto-scale is fine.
        # However, to ensure the curve fits well:
        if y2_max < 0: y2_max = 0.1
        if y2_min > 0: y2_min = -0.1
        
        # Labels and Markers
        # User requested format: 'Residue: {}%'
        residue_label_text = f"Residue: {residue_val:.1f}%"
        
        # Peak label format was not explicitly changed, standard is just temp like "600 °C"
        peak_label_text = f"{peak_temp:.0f} °C" if peak_temp is not None else ""
        
        # Build Option
        option = {
            "title": {
                "text": "instrument_export",
                "left": "center",
                "textStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 16
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"}
            },
            "legend": {
                "data": ["Weight (%)", "DTG (%/°C)"],
                "top": "middle",
                "left": "left",
                "orient": "vertical",
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
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 30,
                "min": min_temp,
                "max": max_temp,
                "splitLine": {"show": False},
                "axisLabel": {
                    "formatter": "{value}"
                }
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "position": "left",
                    "min": y1_min,
                    "max": y1_max,
                    "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
                },
                {
                    "type": "value",
                    "name": "DTG (%/°C)",
                    "position": "right",
                    "min": y2_min,
                    "max": y2_max,
                    "splitLine": {"show": False}
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "smooth": False,
                    "symbol": "none",
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "itemStyle": {"color": "#1f4e9c"},
                    "yAxisIndex": 0,
                    "data": weight_data,
                    "markPoint": {
                        "symbolSize": 10,
                        "label": {
                            "show": True,
                            "formatter": residue_label_text,
                            "position": "top",
                            "distance": 5,
                            "color": "#1f4e9c",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12
                        },
                        "data": [
                            {
                                "coord": [residue_temp, residue_val],
                                "symbol": "circle",
                                "itemStyle": {"color": "#1f4e9c"}
                            }
                        ]
                    }
                },
                {
                    "name": "DTG (%/°C)",
                    "type": "line",
                    "smooth": False,
                    "symbol": "none",
                    "lineStyle": {"color": "#c0392b", "width": 2},
                    "itemStyle": {"color": "#c0392b"},
                    "yAxisIndex": 1,
                    "data": dtg_data,
                    "markPoint": {
                        "symbolSize": 10,
                        "label": {
                            "show": True,
                            "formatter": peak_label_text,
                            "position": "top",
                            "distance": 5,
                            "color": "#c0392b",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12
                        },
                        "data": [
                            {
                                "coord": [peak_temp, -peak_dtg] if peak_temp is not None else [0, 0],
                                "symbol": "triangle",
                                "itemStyle": {"color": "#c0392b"}
                            }
                        ] if peak_temp is not None else []
                    }
                }
            ]
        }
        
        figure_obj = {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        
        output = {"figures": [figure_obj]}
        print(json.dumps(output))
        
    except Exception as e:
        # Fallback empty output on error
        print(json.dumps({"figures": [], "error": str(e)}))

if __name__ == "__main__":
    main()
