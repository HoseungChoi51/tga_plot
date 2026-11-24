import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheets = xl.sheet_names  # ['PE', 'PVC', 'PET']

# Define offsets: PE at 0, PVC shifted up by 20%, PET shifted up by 40% (or down depending on interpretation)
# "겹치지 않게 20%씩 위아래로 띄워서" means offset each curve vertically so they don't overlap.
# We'll shift them in the Y-axis space. Since weight is 0-100%, we can add offsets like +0, +25, +50 or similar.
# But since deriv weight is also present, let's focus on Weight (%) curves only as requested ("무게 곡선").
# Let's assign vertical offsets: PE: 0, PVC: +30, PET: +60 to ensure no overlap visually.

series_data = []
for i, sheet_name in enumerate(sheets):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    temp = df['Temperature (°C)'].tolist()
    weight = df['Weight (%)'].tolist()
    
    # Apply vertical offset: each subsequent curve gets +30 offset
    offset = i * 30
    weighted = [w + offset for w in weight]
    
    series_data.append({
        "name": f"{sheet_name} (offset {offset})",
        "type": "line",
        "data": list(zip(temp, weighted)),
        "smooth": True,
        "showSymbol": False,
        "lineStyle": {"width": 2}
    })

option = {
    "title": {
        "text": "TGA 무게 곡선 비교 (Offset 적용)",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None  # No JS functions allowed
    },
    "legend": {
        "data": [f"{s} (offset {i*30})" for i, s in enumerate(sheets)],
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "8%",
        "right": "5%",
        "bottom": "10%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "무게 (%) / Offset 적용",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": series_data
}

output = {
    "figures": [
        {
            "name": "tga_weight_offset",
            "option": option,
            "width": 800,
            "height": 500,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
