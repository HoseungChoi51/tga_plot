import json
import os
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"


def main():
    df = pd.read_excel(DATA_FILE, sheet_name="Raw")
    df.columns = [str(c).strip() for c in df.columns]

    def find_column(candidates, fallback):
        for col in df.columns:
            low = col.lower()
            if any(token in low for token in candidates):
                return col
        return df.columns[fallback]

    x_col = find_column(["temperature", "temp"], 1)
    weight_col = find_column(["weight"], 2)
    dtg_col = find_column(["deriv", "dtg"], 3)

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        raise ValueError("Raw 시트에서 유효한 온도, 중량, DTG 데이터를 찾을 수 없습니다.")

    residue_idx = int(np.argmin(np.abs(x - 800.0)))
    eligible = np.flatnonzero(x > 150.0)
    peak_idx = int(eligible[np.argmax(-dtg[eligible])]) if len(eligible) else int(np.argmax(-dtg))

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12, "color": "#333333"},
        "title": {
            "text": "Raw",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "fontWeight": "normal"},
        },
        "legend": {"data": ["Weight (%)", "DTG (-×)"], "left": "center", "top": 36},
        "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "inverse": True,
            "min": float(np.nanmin(x)),
            "max": float(np.nanmax(x)),
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisTick": {"show": True},
                "axisLabel": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
            },
            {
                "type": "value",
                "name": "DTG (-×, %/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisTick": {"show": True},
                "axisLabel": {"show": True},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "lineStyle": {"width": 2, "color": "#1f4e9c"},
                "data": [[float(a), float(b)] for a, b in zip(x, weight)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {weight[residue_idx]:.1f}%",
                        "position": "top",
                        "color": "#1f4e9c",
                    },
                    "data": [{"coord": [float(x[residue_idx]), float(weight[residue_idx])]}],
                },
            },
            {
                "name": "DTG (-×)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "lineStyle": {"width": 2, "color": "#c0392b"},
                "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": f"{x[peak_idx]:.0f} °C",
                        "position": "top",
                        "color": "#c0392b",
                    },
                    "data": [{"coord": [float(x[peak_idx]), float(-dtg[peak_idx])]}],
                },
            },
        ],
    }

    print(json.dumps({
        "figures": [{
            "name": "Raw",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }]
    }, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
