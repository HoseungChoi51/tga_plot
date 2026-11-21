import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_residual_weight_at_temp(df, temp_target=700):
    """Find the weight at the closest temperature to target."""
    temps = df['Temperature'].values
    weights = df['Weight(%)'].values
    
    # Find index of closest temperature
    idx = np.argmin(np.abs(temps - temp_target))
    return weights[idx]

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheets_info = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    # Clean column names if needed
    df.columns = [str(c).strip() for c in df.columns]
    
    # Identify columns based on preview info
    # Assuming standard TGA format: Time, Temperature, Weight(%), D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns:
        continue
        
    # Prepare data for chart
    x_data = df[temp_col].tolist()
    y1_data = df[weight_col].tolist()
    y2_data = df[dtg_col].tolist() if dtg_col in df.columns else None
    
    # Calculate residual weight at 700°C
    resid_700 = get_residual_weight_at_temp(df, 700)
    
    sheets_info.append({
        "name": sheet_name,
        "x": x_data,
        "y1": y1_data,
        "y2": y2_data,
        "resid_700": resid_700
    })

# Build ECharts option
series_list = []
legend_data = []

colors = ['#5470c6', '#91cc75', '#fac858'] # Blue, Green, Yellow/Gold

for i, s_info in enumerate(sheets_info):
    color = colors[i % len(colors)]
    label = s_info['name']
    legend_data.append(label)
    
    # TG Series (Left Y-axis)
    series_list.append({
        "name": f"{label} (TG)",
        "type": "line",
        "smooth": True,
        "showSymbol": False,
        "data": [[x, y] for x, y in zip(s_info['x'], s_info['y1'])],
        "yAxisIndex": 0,
        "itemStyle": {"color": color},
        "lineStyle": {"width": 2},
        "markPoint": {
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": color, "borderColor": "#fff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "fontSize": 10,
                "color": "#333"
            },
            "data": [
                {
                    "coord": [700, s_info['resid_700']],
                    "name": f"{round(s_info['resid_700'], 2)}%"
                }
            ]
        }
    })
    
    # DTG Series (Right Y-axis) - usually dashed or thinner
    if s_info['y2']:
        series_list.append({
            "name": f"{label} (DTG)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": [[x, y] for x, y in zip(s_info['x'], s_info['y2'])],
            "yAxisIndex": 1,
            "itemStyle": {"color": color},
            "lineStyle": {"width": 1.5, "type": "dashed"},
            "opacity": 0.7
        })

option = {
    "title": {
        "text": "TGA/DTG Analysis",
        "subtext": "Residual weight at 700 °C shown on TG curves",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": None # Using default axis tooltip which shows all series values
    },
    "legend": {
        "data": legend_data + [f"{l} (DTG)" for l in legend_data],
        "bottom": 0,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
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
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 100,
            "position": "left",
            "splitLine": {"show": True}
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "splitLine": {"show": False}
        }
    ],
    "series": series_list
}

output = {
    "figures": [
        {
            "name": "tga_plot",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
