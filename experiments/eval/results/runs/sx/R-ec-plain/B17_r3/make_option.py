import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheets = ["PE", "PVC", "PET"]

series_list = []
colors = ["#5470c6", "#91cc75", "#fac858"]  # distinct colors for each polymer

for i, sheet in enumerate(sheets):
    df = pd.read_excel(xl, sheet_name=sheet)
    temp = df["Temperature (°C)"].values
    weight = df["Weight (%)"].values
    
    # Apply vertical offset: PE at 0, PVC shifted up by 20%, PET shifted up by 40%
    # This creates a stacked effect so curves don't overlap
    offset = i * 20.0
    weight_offset = weight + offset
    
    # Downsample if too many points (keep under ~500 for performance)
    step = max(1, len(temp) // 400)
    temp_ds = temp[::step]
    weight_ds = weight_offset[::step]
    
    data_points = [[float(t), float(w)] for t, w in zip(temp_ds, weight_ds)]
    
    series_list.append({
        "name": f"{sheet} (offset {int(offset)}%)",
        "type": "line",
        "data": data_points,
        "smooth": True,
        "symbol": "none",
        "lineStyle": {"width": 2},
        "itemStyle": {"color": colors[i]}
    })

option = {
    "title": {
        "text": "TGA Weight Curves with Vertical Offset",
        "left": "center",
        "top": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None
    },
    "legend": {
        "data": [f"{s['name']}" for s in series_list],
        "top": 40,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {
        "left": 60,
        "right": 30,
        "top": 80,
        "bottom": 50
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%) + Offset",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "series": series_list
}

output = {
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

print(json.dumps(output, ensure_ascii=False))
