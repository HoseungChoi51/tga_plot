import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheets_data = {}
for sheet_name in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=sheet_name)
    # Standardize column names based on preview
    cols = df.columns.tolist()
    # Identify columns by name patterns
    temp_col = None
    weight_col = None
    dtg_col = None
    for c in cols:
        if 'Temperature' in str(c):
            temp_col = c
        elif 'Weight (%)' in str(c) or 'Weight(%)' in str(c):
            weight_col = c
        elif 'Deriv' in str(c) or 'DTG' in str(c):
            dtg_col = c
    
    if temp_col and weight_col and dtg_col:
        sheets_data[sheet_name] = {
            'temp': df[temp_col].values,
            'weight': df[weight_col].values,
            'dtg': df[dtg_col].values
        }

figures = []

# Combine all sheets into one plot (겹쳐 그리기)
all_weight = []
all_dtg = []
legend_items = []

for sheet_name, data in sheets_data.items():
    temp = data['temp']
    weight = data['weight']
    dtg = data['dtg']
    
    # Prepare data for ECharts: [x, y] pairs
    # Weight series
    w_pairs = [[float(t), float(w)] for t, w in zip(temp, weight)]
    # DTG series (multiplied by -1 so peaks point up)
    d_pairs = [[float(t), float(-d)] for t, d in zip(temp, dtg)]
    
    all_weight.append({
        "name": f"{sheet_name} Weight",
        "type": "line",
        "data": w_pairs,
        "yAxisIndex": 0,
        "showSymbol": False,
        "lineStyle": {"width": 2},
        "emphasis": {"focus": "series"}
    })
    
    all_dtg.append({
        "name": f"{sheet_name} DTG",
        "type": "line",
        "data": d_pairs,
        "yAxisIndex": 1,
        "showSymbol": False,
        "lineStyle": {"width": 2, "type": "dashed"},
        "emphasis": {"focus": "series"}
    })
    
    legend_items.append(f"{sheet_name} Weight")
    legend_items.append(f"{sheet_name} DTG")

# Calculate residue and peak for each sheet to add markers
residue_markers = []
peak_markers = []

for sheet_name, data in sheets_data.items():
    temp = data['temp']
    weight = data['weight']
    dtg = data['dtg']
    
    # Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temp - 800))
    res_val = weight[idx_800]
    res_temp = temp[idx_800]
    residue_markers.append({
        "coord": [float(res_temp), float(res_val)],
        "value": f"Residue {res_val:.1f}%"
    })
    
    # Peak: highest DTG above 150°C (note: we multiplied by -1, so max of -dtg is min of dtg)
    mask = temp > 150
    if np.any(mask):
        dtg_above = dtg[mask]
        temp_above = temp[mask]
        # Find index of minimum dtg (which becomes maximum after * -1)
        min_idx = np.argmin(dtg_above)
        peak_temp = temp_above[min_idx]
        peak_val = -dtg_above[min_idx]  # value on the plotted axis
        peak_markers.append({
            "coord": [float(peak_temp), float(peak_val)],
            "value": f"{peak_temp:.0f}°C"
        })

# Build option
option = {
    "title": {
        "text": "TGA Comparison: PE, PVC, PET",
        "left": "center",
        "top": 10,
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
        "orient": "vertical",
        "right": 10,
        "top": "middle",
        "data": legend_items,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        }
    },
    "grid": {
        "left": 70,
        "right": 180,
        "bottom": 60,
        "top": 80,
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "min": 30,
        "max": 900,
        "axisLine": {"onZero": False},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": "#eee"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "left",
            "min": 0,
            "max": 100,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"formatter": "{value}%", "fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        },
        {
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "right",
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        }
    ],
    "series": all_weight + all_dtg
}

# Add scatter points for residues and peaks
scatter_residue = {
    "name": "Residue",
    "type": "scatter",
    "symbolSize": 8,
    "itemStyle": {"color": "#1f4e9c"},
    "label": {
        "show": True,
        "position": "top",
        "fontFamily": "Noto Sans CJK KR",
        "fontSize": 10
    },
    "data": []
}

# For residue labels, we need to include the label text in the data item
for rm in residue_markers:
    coord = rm["coord"]
    val_str = rm["value"]
    scatter_residue["data"].append({
        "value": coord,
        "label": {"formatter": val_str}
    })

scatter_peak = {
    "name": "Peak",
    "type": "scatter",
    "yAxisIndex": 1,
    "symbolSize": 8,
    "itemStyle": {"color": "#c0392b"},
    "label": {
        "show": True,
        "position": "top",
        "fontFamily": "Noto Sans CJK KR",
        "fontSize": 10
    },
    "data": []
}

for pm in peak_markers:
    coord = pm["coord"]
    val_str = pm["value"]
    scatter_peak["data"].append({
        "value": coord,
        "label": {"formatter": val_str}
    })

option["series"].append(scatter_residue)
option["series"].append(scatter_peak)

fig = {
    "name": "tga_combined",
    "option": option,
    "width": 800,
    "height": 500,
    "dpi": 300,
    "formats": ["png"]
}

figures.append(fig)

output = {"figures": figures}
print(json.dumps(output, ensure_ascii=False))
