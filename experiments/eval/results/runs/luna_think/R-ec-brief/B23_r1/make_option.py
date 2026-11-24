import json
import os
import re
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

SAMPLE_COLORS = {
    "Raw": "#000000",
    "Acid-washed": "#2878c8",
    "Annealed": "#c0392b",
}


def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip())


def get_column(df, pattern, fallback_index):
    for col in df.columns:
        if re.search(pattern, str(col), flags=re.IGNORECASE):
            return pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
    if fallback_index < df.shape[1]:
        return pd.to_numeric(df.iloc[:, fallback_index], errors="coerce").to_numpy(dtype=float)
    return np.array([], dtype=float)


def main():
    file_path = os.environ.get("DATA_FILE", DATA_FILE)
    sheets = pd.read_excel(file_path, sheet_name=None)

    series = []
    x_values_all = []
    weight_values_all = []
    dtg_values_all = []

    for sheet_name, df in sheets.items():
        name = clean_name(sheet_name)
        if name not in SAMPLE_COLORS or df.empty:
            continue

        x = get_column(df, r"temperature", 1)
        weight = get_column(df, r"weight\s*\(%\)", 2)
        dtg = get_column(df, r"deriv", 3)

        n = min(len(x), len(weight), len(dtg))
        x, weight, dtg = x[:n], weight[:n], dtg[:n]
        valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
        x, weight, dtg = x[valid], weight[valid], dtg[valid]
        if len(x) == 0:
            continue

        order = np.argsort(x)
        x, weight, dtg = x[order], weight[order], dtg[order]
        color = SAMPLE_COLORS[name]

        residue_index = int(np.argmin(np.abs(x - 800)))
        residue_x = float(x[residue_index])
        residue_y = float(weight[residue_index])

        peak_candidates = np.flatnonzero(x > 150)
        if len(peak_candidates):
            peak_index = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
            peak_x = float(x[peak_index])
            peak_y = float(-dtg[peak_index])
        else:
            peak_x = float(x[-1])
            peak_y = float(-dtg[-1])

        series.append({
            "name": f"{name} Weight",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"color": color, "width": 2},
            "itemStyle": {"color": color},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_y:.1f}%",
                    "position": "top",
                    "color": color,
                    "fontSize": 11,
                },
                "data": [{"coord": [residue_x, residue_y]}],
            },
        })
        series.append({
            "name": f"{name} DTG",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"color": color, "width": 1.8, "type": "dashed"},
            "itemStyle": {"color": color},
            "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
            "markPoint": {
                "symbol": "diamond",
                "symbolSize": 9,
                "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"{peak_x:.0f} °C",
                    "position": "top",
                    "color": color,
                    "fontSize": 11,
                },
                "data": [{"coord": [peak_x, peak_y]}],
            },
        })

        x_values_all.extend(x.tolist())
        weight_values_all.extend(weight.tolist())
        dtg_values_all.extend((-dtg).tolist())

    option = {
        "title": {
            "text": "TGA Comparison",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": [
                f"{name} {kind}"
                for name in SAMPLE_COLORS
                for kind in ("Weight", "DTG")
                if any(s["name"] == f"{name} {kind}" for s in series)
            ],
            "left": 12,
            "top": "middle",
            "orient": "vertical",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 10},
        },
        "grid": {"left": 78, "right": 78, "top": 62, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 36,
            "min": float(np.nanmin(x_values_all)) if x_values_all else 0,
            "max": float(np.nanmax(x_values_all)) if x_values_all else 900,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            {
                "type": "value",
                "name": "−DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
        ],
        "series": series,
    }

    result = {
        "figures": [{
            "name": "tga_comparison",
            "option": option,
            "width": 900,
            "height": 600,
            "dpi": 300,
            "formats": ["png"],
        }]
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
