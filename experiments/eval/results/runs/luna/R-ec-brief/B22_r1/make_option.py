import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "temperature" in c.lower() or "온도" in c)
weight_col = next(c for c in df.columns if "weight" in c.lower() and ("deriv" not in c.lower() and "derivative" not in c.lower()) or "무게" in c.lower())
dtg_col = next(c for c in df.columns if "deriv" in c.lower() or "dtg" in c.lower())

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy(dtype=float)
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
order = np.argsort(temperature)
temperature, weight, dtg = temperature[order], weight[order], dtg[order]

baseline_index = int(np.argmin(np.abs(temperature - 150.0)))
baseline_weight = weight[baseline_index]
if not np.isfinite(baseline_weight) or baseline_weight == 0:
    raise ValueError("150 °C 기준 무게가 유효하지 않습니다.")

dry_weight = weight / baseline_weight * 100.0
peak_candidates = np.where(temperature > 150.0)[0]
peak_index = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
residue_index = int(np.argmin(np.abs(temperature - 800.0)))

def clean_number(value):
    value = float(value)
    return value if np.isfinite(value) else None

option = {
    "backgroundColor": "#ffffff",
    "animation": False,
    "title": {
        "text": "Raw",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "color": "#222222"},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["건조 기준 무게", "DTG (-)"],
        "left": "center",
        "bottom": 8,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
    },
    "grid": {"left": 72, "right": 72, "top": 58, "bottom": 70},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 32,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True, "fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 110,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisTick": {"show": True},
            "axisLabel": {"show": True, "fontFamily": "Noto Sans CJK KR", "fontSize": 11},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "inverse": False,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisTick": {"show": True},
            "axisLabel": {"show": True, "fontFamily": "Noto Sans CJK KR", "fontSize": 11},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "건조 기준 무게",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "data": [[clean_number(x), clean_number(y)] for x, y in zip(temperature, dry_weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {dry_weight[residue_index]:.1f}%",
                    "position": "right",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                },
                "data": [{
                    "coord": [
                        clean_number(temperature[residue_index]),
                        clean_number(dry_weight[residue_index]),
                    ]
                }],
            },
        },
        {
            "name": "DTG (-)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": "#c0392b"},
            "data": [[clean_number(x), clean_number(-y)] for x, y in zip(temperature, dtg)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{temperature[peak_index]:.0f} °C",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                },
                "data": [{
                    "coord": [
                        clean_number(temperature[peak_index]),
                        clean_number(-dtg[peak_index]),
                    ]
                }],
            },
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "plot1",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
