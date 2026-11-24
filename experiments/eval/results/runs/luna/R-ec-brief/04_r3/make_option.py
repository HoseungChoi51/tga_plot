import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

def main():
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    cols = list(df.columns)

    def find_column(pattern, fallback):
        for col in cols:
            if re.search(pattern, str(col), re.IGNORECASE):
                return col
        return cols[fallback]

    x_col = find_column(r"temperature|temp", 1)
    weight_col = find_column(r"weight", 2)
    dtg_col = find_column(r"d\.?\s*w|dtg|derivative", 3)

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if not len(x):
        raise ValueError("유효한 TGA 데이터가 없습니다.")

    residue_idx = int(np.argmin(np.abs(x - 800)))
    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
        peak_temp = x[peak_idx]
        peak_value = -dtg[peak_idx]
        peak_label = f"{peak_temp:.0f} °C"
    else:
        peak_idx = None
        peak_value = None
        peak_label = ""

    series = [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {weight[residue_idx]:.1f}%",
                    "position": "right",
                    "color": "#1f4e9c",
                },
                "data": [{"coord": [float(x[residue_idx]), float(weight[residue_idx])]}],
            },
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#c0392b"},
        },
    ]

    if peak_idx is not None:
        series[1]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": peak_label,
                "position": "top",
                "color": "#c0392b",
            },
            "data": [{"coord": [float(x[peak_idx]), float(peak_value)]}],
        }

    option = {
        "animation": False,
        "title": {
            "text": "CNT 산화 거동",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 18,
                "color": "#000080",
                "fontWeight": "normal",
            },
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight (%)", "-DTG (%/°C)"], "left": "center"},
        "grid": {"left": 75, "right": 75, "top": 75, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 35,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 50,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 50,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
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

if __name__ == "__main__":
    main()
