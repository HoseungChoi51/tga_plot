import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_residual_at_700(df, temp_col='Temperature', weight_col='Weight(%)'):
    """Find the residual weight at 700°C by interpolation."""
    # Sort by temperature just in case
    df_sorted = df.sort_values(by=temp_col)
    
    # Find indices around 700
    temps = df_sorted[temp_col].values
    weights = df_sorted[weight_col].values
    
    if temps[-1] < 700:
        return round(weights[-1], 2)
    if temps[0] > 700:
        return round(weights[0], 2)
        
    # Interpolate
    idx = (temps - 700).searchsorted(0)
    if idx == 0:
        return round(weights[0], 2)
    elif idx >= len(temps):
        return round(weights[-1], 2)
    else:
        t1, t2 = temps[idx-1], temps[idx]
        w1, w2 = weights[idx-1], weights[idx]
        if t2 == t1:
            return round(w1, 2)
        interp_w = w1 + (w2 - w1) * (700 - t1) / (t2 - t1)
        return round(interp_w, 2)

sheets_info = []
xls = pd.ExcelFile(DATA_FILE)
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    # Clean column names if needed, assuming standard based on preview
    cols = df.columns.tolist()
    # Map based on typical TGA structure from preview
    # A: Time, B: Temperature, C: Weight(%), D: D.W(%/C)
    if len(cols) >= 4:
        temp_col = cols[1]
        weight_col = cols[2]
        dw_col = cols[3]
        
        residual = get_residual_at_700(df, temp_col, weight_col)
        
        # Prepare data for ECharts
        # Downsample slightly if too many points to keep JSON manageable, but 800 is fine.
        x_data = df[temp_col].round(2).tolist()
        y_weight = df[weight_col].round(2).tolist()
        y_dw = df[dw_col].round(4).tolist()
        
        series_item = {
            "name": f"{sheet_name} (Residual @700°C: {residual}%)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": [[x, y] for x, y in zip(x_data, y_weight)],
            "yAxisIndex": 0,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"}
        }
        
        sheets_info.append({
            "name": sheet_name,
            "series": series_item,
            "residual": residual
        })

# Build ECharts Option
option = {
    "backgroundColor": "#ffffff",
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": None # Default formatter handles array of series well
    },
    "legend": {
        "data": [s["series"]["name"] for s in sheets_info],
        "top": "5%",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "toolbox": {
        "feature": {
            "saveAsImage": {},
            "dataZoom": {},
            "restore": {}
        }
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "axisLabel": {"formatter": "{value}"},
        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLine": {"onZero": False},
            "splitLine": {"lineStyle": {"color": "#eee"}}
        }
    ],
    "series": [s["series"] for s in sheets_info]
}

result = {
    "figures": [
        {
            "name": "tga_residual_700c",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
