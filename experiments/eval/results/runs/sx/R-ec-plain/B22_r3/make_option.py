import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the 'Raw' sheet
df = pd.read_excel(DATA_FILE, sheet_name='Raw')

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values

# Find the weight at 150 °C for normalization
# Interpolate to find weight at exactly 150 °C
import numpy as np
idx_150 = np.searchsorted(temp, 150)
if idx_150 == 0:
    w_150 = weight[0]
elif idx_150 >= len(temp):
    w_150 = weight[-1]
else:
    # Linear interpolation between idx_150-1 and idx_150
    t1, t2 = temp[idx_150 - 1], temp[idx_150]
    w1, w2 = weight[idx_150 - 1], weight[idx_150]
    if t2 == t1:
        w_150 = w1
    else:
        w_150 = w1 + (w2 - w1) * (150 - t1) / (t2 - t1)

# Normalize weight so that at 150 °C it is 100%
normalized_weight = (weight / w_150) * 100.0

# Prepare data points for ECharts
data_points = []
for t, w in zip(temp, normalized_weight):
    data_points.append([float(t), float(w)])

# Build the ECharts option
option = {
    "title": {
        "text": "TGA Curve (Raw, Normalized at 150°C)",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None
    },
    "legend": {
        "data": ["Normalized Weight"],
        "top": 30
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "10%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": 0,
        "max": 110
    },
    "series": [
        {
            "name": "Normalized Weight",
            "type": "line",
            "showSymbol": False,
            "smooth": True,
            "data": data_points,
            "lineStyle": {
                "width": 2
            }
        }
    ]
}

result = {
    "figures": [
        {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
