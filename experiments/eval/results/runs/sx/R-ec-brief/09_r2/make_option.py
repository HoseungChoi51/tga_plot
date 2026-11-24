import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def make_tga_chart(df, sheet_name):
    # Identify columns based on the preview structure
    x_col = "Temperature"
    y1_col = "Weight(%)"
    y2_col = "D.W(%/C)"
    
    # Extract data
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Prepare DTG: multiply by -1 so peaks point up
    dtg_neg = dtg * -1
    
    # Find Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    residue_temp = temp[idx_800]
    
    # Find Peak: highest DTG peak above 150°C
    mask_peak = temp > 150
    if np.any(mask_peak):
        dtg_filtered = dtg[mask_peak]
        temp_filtered = temp[mask_peak]
        idx_max_dtg = np.argmax(dtg_filtered) # Max of original negative DTG (most negative) -> Min value
        # Wait, "highest DTG peak" usually means the magnitude of mass loss rate. 
        # Since DTG is negative during loss, the "peak" in a standard plot (where we flip sign or look for min) 
        # corresponds to the minimum value of the raw DTG column.
        # The user request says "multiplied by -1 so its peaks point up".
        # So we look for the maximum of (-DTG) which is equivalent to the minimum of DTG.
        
        # Let's re-evaluate:
        # Raw DTG is negative. We plot -DTG.
        # We want the temperature where -DTG is maximum (which is where DTG is minimum/most negative).
        
        neg_dtg_filtered = dtg_filtered * -1
        idx_max_neg = np.argmax(neg_dtg_filtered)
        peak_temp = temp_filtered[idx_max_neg]
        peak_val_neg = neg_dtg_filtered[idx_max_neg]
    else:
        peak_temp = None
        peak_val_neg = None

    # Axis ranges and ticks
    x_min, x_max = np.min(temp), np.max(temp)
    y1_min, y1_max = np.min(weight), np.max(weight)
    y2_min, y2_max = np.min(dtg_neg), np.max(dtg_neg)
    
    # Add some padding
    x_range = x_max - x_min
    y1_range = y1_max - y1_min
    y2_range = y2_max - y2_min
    
    x_axis_min = max(0, x_min - x_range * 0.05)
    x_axis_max = x_max + x_range * 0.05
    y1_axis_min = max(0, y1_min - y1_range * 0.05)
    y1_axis_max = y1_max + y1_range * 0.05
    y2_axis_min = y2_min - abs(y2_range) * 0.05
    y2_axis_max = y2_max + abs(y2_range) * 0.05

    # Series Data
    series_weight = []
    series_dtg = []
    
    for t, w, d in zip(temp, weight, dtg_neg):
        series_weight.append([float(t), float(w)])
        series_dtg.append([float(t), float(d)])
        
    # Markers for annotations
    markers = []
    if len(series_weight) > 0:
         # Residue marker
         markers.append({
            "coord": [float(residue_temp), float(residue_val)],
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
         
    if peak_temp is not None:
        # Peak marker on DTG curve (y2 axis)
        # Need to find the corresponding y value on the plotted dtg_neg curve at peak_temp
        # Since we have discrete points, we use the one closest to peak_temp
        idx_peak = np.argmin(np.abs(temp - peak_temp))
        peak_y_val = dtg_neg[idx_peak]
        
        markers.append({
            "coord": [float(peak_temp), float(peak_y_val)],
            "symbol": "diamond",
            "symbolSize": 6,
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
            "textStyle": {"fontSize": 14, "fontWeight": "bold"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "DTG (%/°C)"],
            "left": "left",
            "top": "middle",
            "orient": "vertical"
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
            "min": round(x_axis_min, 2),
            "max": round(x_axis_max, 2),
            "axisTick": {
                "show": True,
                "alignWithLabel": False,
                "length": 5,
                "lineStyle": {"width": 1, "color": "#333"}
            },
            "axisLabel": {
                "fontSize": 9,
                "margin": 8
            },
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": round(y1_axis_min, 2),
                "max": round(y1_axis_max, 2),
                "axisTick": {
                    "show": True,
                    "alignWithLabel": False,
                    "length": 5,
                    "lineStyle": {"width": 1, "color": "#333"}
                },
                "axisLabel": {
                    "fontSize": 9,
                    "margin": 8
                },
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": round(y2_axis_min, 4),
                "max": round(y2_axis_max, 4),
                "axisTick": {
                    "show": True,
                    "alignWithLabel": False,
                    "length": 5,
                    "lineStyle": {"width": 1, "color": "#333"}
                },
                "axisLabel": {
                    "fontSize": 9,
                    "margin": 8
                },
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": series_weight,
                "yAxisIndex": 0,
                "showSymbol": False,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "markPoint": {
                    "data": [m for m in markers if m["itemStyle"]["color"] == "#1f4e9c"]
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": series_dtg,
                "yAxisIndex": 1,
                "showSymbol": False,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "markPoint": {
                    "data": [m for m in markers if m["itemStyle"]["color"] == "#c0392b"]
                }
            }
        ]
    }
    
    return option

def main():
    figures = []
    
    # Read Excel file
    xls = pd.ExcelFile(DATA_FILE)
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Clean column names just in case
        df.columns = [str(c).strip() for c in df.columns]
        
        # Check if required columns exist
        if "Temperature" in df.columns and "Weight(%)" in df.columns and "D.W(%/C)" in df.columns:
            opt = make_tga_chart(df, sheet_name)
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
    print(json.dumps(output))

if __name__ == "__main__":
    main()
