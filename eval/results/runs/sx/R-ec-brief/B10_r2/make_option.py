import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def main():
    # Read the specific sheet 'Annealed'
    df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
    
    # Identify columns based on standard TGA naming from preview
    x_col = "Temperature (°C)"
    y1_col = "Weight (%)"
    y2_col = "Deriv. Weight (%/°C)"
    
    # Extract data
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Prepare data for ECharts: list of [x, y] pairs
    # Filter out NaN if any exist to be safe, though preview looks clean
    mask_w = ~np.isnan(weight) & ~np.isnan(temp)
    data_weight = [[float(t), float(w)] for t, w in zip(temp[mask_w], weight[mask_w])]
    
    mask_d = ~np.isnan(dtg) & ~np.isnan(temp)
    # DTG is multiplied by -1 so peaks point up
    data_dtg = [[float(t), float(-d)] for t, d in zip(temp[mask_d], dtg[mask_d])]
    
    # Calculate Residue at 800 °C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_temp = temp[idx_800]
    residue_weight = weight[idx_800]
    residue_label = f"Residue {residue_weight:.1f}%"
    
    # Find highest DTG peak above 150 °C
    # We look for the minimum value in original DTG (which becomes maximum after *-1)
    # So we find max of (-dtg) where temp > 150
    valid_peak_mask = (temp > 150) & (~np.isnan(dtg))
    if np.any(valid_peak_mask):
        neg_dtg_vals = -dtg[valid_peak_mask]
        temps_valid = temp[valid_peak_mask]
        
        max_idx_local = np.argmax(neg_dtg_vals)
        peak_temp = temps_valid[max_idx_local]
        peak_val_neg = neg_dtg_vals[max_idx_local] # This is the height of the plotted peak
        
        peak_label = f"{peak_temp:.0f} °C"
    else:
        peak_temp = None
        peak_val_neg = None
        peak_label = ""

    # Figure size: 3.5 x 2.6 inches -> pixels at 96 dpi
    width_px = int(3.5 * 96)
    height_px = int(2.6 * 96)
    
    # Colors for black and white print
    color_line = "#000000"
    color_text = "#000000"
    color_grid = "#cccccc"
    
    # Series Data
    series = []
    
    # Weight Line (y1)
    series.append({
        "name": "Weight (%)",
        "type": "line",
        "yAxisIndex": 0,
        "data": data_weight,
        "lineStyle": {"color": color_line, "width": 1},
        "itemStyle": {"color": color_line},
        "showSymbol": False,
        "smooth": False
    })
    
    # DTG Line (y2)
    series.append({
        "name": "DTG",
        "type": "line",
        "yAxisIndex": 1,
        "data": data_dtg,
        "lineStyle": {"color": color_line, "width": 1, "type": "dashed"},
        "itemStyle": {"color": color_line},
        "showSymbol": False,
        "smooth": False
    })
    
    # Markers for Residue and Peak
    mark_data = []
    if not np.isnan(residue_weight):
        mark_data.append({
            "coord": [float(residue_temp), float(residue_weight)],
            "label": {
                "formatter": residue_label,
                "position": "top",
                "fontSize": 8,
                "color": color_text
            },
            "symbol": "circle",
            "symbolSize": 4,
            "itemStyle": {"color": color_line}
        })
        
    if peak_temp is not None:
        # The peak coordinate needs to be on the DTG curve (y2 axis)
        # But since it's a separate series, we add a scatter or markPoint on that series?
        # Easier: Add a separate scatter series for markers to control z-index and labels easily, 
        # OR add markPoint to the respective series.
        pass

    # Let's use markPoint on the respective series for cleaner association
    # Update Weight series with residue marker
    series[0]["markPoint"] = {
        "data": [{
            "coord": [float(residue_temp), float(residue_weight)],
            "label": {
                "formatter": residue_label,
                "position": "top",
                "fontSize": 8,
                "color": color_text,
                "offset": [0, -5]
            },
            "symbol": "circle",
            "symbolSize": 5,
            "itemStyle": {"color": color_line, "borderColor": color_line}
        }]
    }
    
    # Update DTG series with peak marker
    if peak_temp is not None:
        series[1]["markPoint"] = {
            "data": [{
                "coord": [float(peak_temp), float(peak_val_neg)],
                "label": {
                    "formatter": peak_label,
                    "position": "top",
                    "fontSize": 8,
                    "color": color_text,
                    "offset": [0, -5]
                },
                "symbol": "triangle",
                "symbolSize": 6,
                "itemStyle": {"color": color_line, "borderColor": color_line}
            }]
        }

    option = {
        "title": {
            "text": "Annealed",
            "left": "center",
            "textStyle": {
                "fontSize": 10,
                "fontWeight": "bold",
                "color": color_text
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "DTG"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {
                "fontSize": 8,
                "color": color_text
            }
        },
        "grid": {
            "left": "15%",
            "right": "15%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 25,
            "nameTextStyle": {
                "fontSize": 8,
                "color": color_text
            },
            "axisLabel": {
                "fontSize": 8,
                "color": color_text
            },
            "axisLine": {"lineStyle": {"color": color_text}},
            "splitLine": {"show": True, "lineStyle": {"color": color_grid}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 30,
                "nameTextStyle": {
                    "fontSize": 8,
                    "color": color_text
                },
                "axisLabel": {
                    "fontSize": 8,
                    "color": color_text
                },
                "axisLine": {"lineStyle": {"color": color_text}},
                "splitLine": {"show": True, "lineStyle": {"color": color_grid}}
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 30,
                "nameTextStyle": {
                    "fontSize": 8,
                    "color": color_text
                },
                "axisLabel": {
                    "fontSize": 8,
                    "color": color_text
                },
                "axisLine": {"lineStyle": {"color": color_text}},
                "splitLine": {"show": False}
            }
        ],
        "series": series
    }

    figure = {
        "name": "plot1",
        "option": option,
        "width": width_px,
        "height": height_px,
        "dpi": 600,
        "formats": ["png"]
    }
    
    output = {"figures": [figure]}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
