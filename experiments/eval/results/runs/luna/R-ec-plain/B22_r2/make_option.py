import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)
temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")

valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)

# Use the measured weight at 150 °C as the dry-basis reference.
reference_weight = float(np.interp(150.0, temperature, weight))
dry_basis_weight = weight / reference_weight * 100.0

data = [
    [float(x), float(y)]
    for x, y in zip(temperature, dry_basis_weight)
    if np.isfinite(x) and np.isfinite(y)
]

option = {
    "backgroundColor": "#ffffff",
    "animation": False,
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "color": "#222222"
    },
    "title": {
        "text": "Raw 시료 TGA (150 °C 건조 기준)",
        "subtext": f"150 °C 기준 무게: {reference_weight:.3f}%",
        "left": "center",
        "top": 10,
        "textStyle": {"fontSize": 17, "fontWeight": "bold"},
        "subtextStyle": {"fontSize": 12, "color": "#666666"}
    },
    "grid": {"left": 78, "right": 30, "top": 82, "bottom": 68},
    "tooltip": {
        "trigger": "axis",
        "valueFormatter": "{value}",
        "axisPointer": {"type": "cross"}
    },
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "yAxis": {
        "type": "value",
        "name": "건조 기준 무게 (%)",
        "nameLocation": "middle",
        "nameGap": 58,
        "min": 0,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "series": [{
        "name": "Raw",
        "type": "line",
        "data": data,
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {"width": 2, "color": "#2563a6"},
        "itemStyle": {"color": "#2563a6"},
        "markLine": {
            "symbol": ["none", "none"],
            "lineStyle": {"type": "dashed", "color": "#888888", "width": 1},
            "label": {"show": True, "formatter": "150 °C 기준", "position": "insideEndTop"},
            "data": [{"xAxis": 150}]
        }
    }]
}

print(json.dumps({
    "figures": [{
        "name": "raw_dry_basis_150C",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
