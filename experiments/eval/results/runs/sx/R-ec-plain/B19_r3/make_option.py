import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read PVC sheet
df_pvc = pd.read_excel(DATA_FILE, sheet_name="PVC")

# Rename columns for easier access
df_pvc.columns = ["Time", "Temperature", "Weight", "Deriv_Weight"]

# Filter data between 200 and 400 °C
mask = (df_pvc["Temperature"] >= 200) & (df_pvc["Temperature"] <= 400)
df_range = df_pvc[mask]

if len(df_range) == 0:
    # Fallback: use closest points if exact range not found
    idx_200 = df_pvc["Temperature"].sub(200).abs().idxmin()
    idx_400 = df_pvc["Temperature"].sub(400).abs().idxmin()
    weight_at_200 = df_pvc.loc[idx_200, "Weight"]
    weight_at_400 = df_pvc.loc[idx_400, "Weight"]
else:
    weight_at_200 = df_range.iloc[0]["Weight"]
    weight_at_400 = df_range.iloc[-1]["Weight"]

mass_loss = weight_at_200 - weight_at_400

# Prepare full TGA data for plotting
x_temp = df_pvc["Temperature"].tolist()
y_weight = df_pvc["Weight"].tolist()
y_deriv = df_pvc["Deriv_Weight"].tolist()

# Downsample for performance if needed (keep every 5th point roughly)
step = max(1, len(x_temp) // 300)
x_down = x_temp[::step]
y_w_down = y_weight[::step]
y_d_down = y_deriv[::step]

# Ensure last point is included
if x_temp[-1] != x_down[-1]:
    x_down.append(x_temp[-1])
    y_w_down.append(y_weight[-1])
    y_d_down.append(y_deriv[-1])

option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": f"PVC TGA Analysis (Mass Loss 200-400°C: {mass_loss:.2f}%)",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "bottom": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": [
        {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 30,
            "max": 900,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        }
    ],
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "min": 0,
            "max": 105,
            "axisLabel": {"formatter": "{value}%"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "position": "right",
            "min": -3,
            "max": 1,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#5470c6"},
            "itemStyle": {"color": "#5470c6"},
            "data": [[t, w] for t, w in zip(x_down, y_w_down)],
            "markArea": {
                "silent": True,
                "itemStyle": {
                    "color": "rgba(255, 173, 177, 0.2)"
                },
                "label": {
                    "show": True,
                    "position": "insideTop",
                    "formatter": f"ΔW = {mass_loss:.2f}%",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12,
                    "color": "#d62728"
                },
                "data": [
                    [{"xAxis": 200}, {"xAxis": 400}]
                ]
            }
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#ee6666"},
            "itemStyle": {"color": "#ee6666"},
            "data": [[t, d] for t, d in zip(x_down, y_d_down)]
        }
    ]
}

result = {
    "figures": [
        {
            "name": "pvc_tga_mass_loss",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
