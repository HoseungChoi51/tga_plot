import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def make_tga_option(df, sheet_name):
    # Extract data
    temp = df['Temperature (°C)'].values
    weight = df['Weight (%)'].values
    dtg = df['Deriv. Weight (%/°C)'].values
    
    # Prepare series data for TGA curve (weight vs temp)
    tga_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
    
    # Prepare series data for DTG curve (-DTG vs temp)
    dtg_data = [[float(t), -float(d)] for t, d in zip(temp, dtg)]
    
    # Find residue at 800°C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_temp = temp[idx_800]
    residue_weight = weight[idx_800]
    
    # Find peak temperature above 150°C (highest DTG peak means most negative DTG, so max of -DTG)
    mask_above_150 = temp > 150
    if np.any(mask_above_150):
        dtg_neg = -dtg[mask_above_150]
        temps_above_150 = temp[mask_above_150]
        peak_idx_local = np.argmax(dtg_neg)
        peak_temp = temps_above_150[peak_idx_local]
        peak_dtg_val = dtg_neg[peak_idx_local]
    else:
        peak_temp = None
        peak_dtg_val = None

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
            "textStyle": {"fontSize": 16}
        },
        "tooltip": {
            "trigger": "axis"
        },
        "legend": {
            "data": ["Weight (%)", "-DTG"],
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
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLine": {"show": True},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLine": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "position": "right",
                "axisLine": {"show": True},
                "splitLine": {"show": False}
            }
        ],
        "series": []
    }
    
    # Weight series
    weight_series = {
        "name": "Weight (%)",
        "type": "line",
        "data": tga_data,
        "yAxisIndex": 0,
        "lineStyle": {"color": "#1f4e9c", "width": 2},
        "itemStyle": {"color": "#1f4e9c"},
        "symbol": "none",
        "markLine": {},
        "markPoint": {}
    }
    
    # Add horizontal reference line at 50% weight if it's the Raw sheet
    if sheet_name == "Raw":
        weight_series["markLine"] = {
            "silent": True,
            "symbol": "none",
            "lineStyle": {
                "color": "#666",
                "type": "dashed",
                "width": 1
            },
            "data": [
                {
                    "yAxis": 50,
                    "label": {
                        "formatter": "50%",
                        "position": "end"
                    }
                }
            ]
        }
        
        # Add annotation text in top right
        # Using graphic element for fixed position text
        option["graphic"] = [
            {
                "type": "text",
                "right": 50,
                "top": 40,
                "style": {
                    "text": "공기, 10 °C/min",
                    "fill": "#333",
                    "fontSize": 12
                }
            }
        ]

    # Add residue marker
    weight_series["markPoint"] = {
        "data": [
            {
                "coord": [float(residue_temp), float(residue_weight)],
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "right",
                    "distance": 5,
                    "fontSize": 10
                }
            }
        ]
    }
    
    # DTG series
    dtg_series = {
        "name": "-DTG",
        "type": "line",
        "data": dtg_data,
        "yAxisIndex": 1,
        "lineStyle": {"color": "#c0392b", "width": 2},
        "itemStyle": {"color": "#c0392b"},
        "symbol": "none",
        "markPoint": {}
    }
    
    # Add peak marker
    if peak_temp is not None:
        dtg_series["markPoint"] = {
            "data": [
                {
                    "coord": [float(peak_temp), float(peak_dtg_val)],
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": f"{peak_temp:.0f} °C",
                        "position": "top",
                        "distance": 5,
                        "fontSize": 10
                    }
                }
            ]
        }
        
    option["series"].append(weight_series)
    option["series"].append(dtg_series)
    
    return option

figures = []

# Read Excel file
xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    # Ensure column names match expectations from preview
    expected_cols = ['Time (min)', 'Temperature (°C)', 'Weight (%)', 'Deriv. Weight (%/°C)']
    if all(col in df.columns for col in expected_cols):
        opt = make_tga_option(df, sheet_name)
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
