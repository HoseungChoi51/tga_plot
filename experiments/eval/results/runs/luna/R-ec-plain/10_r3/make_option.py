import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
TARGET_TEMP = 700.0


def clean_num(value):
    try:
        value = float(value)
        return value if np.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def main():
    xls = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]

        temp_col = next((c for c in df.columns if "temp" in c.lower()), None)
        weight_col = next(
            (c for c in df.columns if "weight" in c.lower() or "mass" in c.lower()),
            None,
        )
        derivative_col = next(
            (c for c in df.columns if re.search(r"d\.?\s*w|deriv", c.lower())),
            None,
        )
        if temp_col is None or weight_col is None:
            continue

        temps = pd.to_numeric(df[temp_col], errors="coerce").to_numpy(dtype=float)
        weights = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(temps) & np.isfinite(weights)
        temps, weights = temps[valid], weights[valid]
        if not len(temps):
            continue

        order = np.argsort(temps)
        temps, weights = temps[order], weights[order]
        residue = float(np.interp(TARGET_TEMP, temps, weights))

        series = [{
            "name": "Weight",
            "type": "line",
            "data": [[clean_num(x), clean_num(y)] for x, y in zip(temps, weights)],
            "showSymbol": False,
            "lineStyle": {"width": 2},
            "yAxisIndex": 0,
        }]

        y_axes = [{
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 105,
            "axisLabel": {"formatter": "{value}%"},
            "nameLocation": "middle",
            "nameGap": 48,
        }]

        if derivative_col is not None:
            dtemps = pd.to_numeric(df[ temp_col ], errors="coerce").to_numpy(dtype=float)
            deriv = pd.to_numeric(df[derivative_col], errors="coerce").to_numpy(dtype=float)
            dvalid = np.isfinite(dtemps) & np.isfinite(deriv)
            dtemps, deriv = dtemps[dvalid], deriv[dvalid]
            dorder = np.argsort(dtemps)
            dtemps, deriv = dtemps[dorder], deriv[dorder]
            if len(dtemps):
                series.append({
                    "name": "Derivative",
                    "type": "line",
                    "data": [[clean_num(x), clean_num(y)] for x, y in zip(dtemps, deriv)],
                    "showSymbol": False,
                    "lineStyle": {"width": 1.5, "type": "dashed"},
                    "yAxisIndex": 1,
                })
                y_axes.append({
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "position": "right",
                    "scale": True,
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "splitLine": {"show": False},
                })

        option = {
            "animation": False,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            "title": {
                "text": str(sheet),
                "subtext": f"잔류량 @ {TARGET_TEMP:.0f} °C: {residue:.2f}%",
                "left": "center",
            },
            "tooltip": {"trigger": "axis"},
            "legend": {"top": 48},
            "grid": {"left": 78, "right": 78 if len(y_axes) > 1 else 30, "top": 100, "bottom": 62},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": float(np.nanmin(temps)),
                "max": float(np.nanmax(temps)),
            },
            "yAxis": y_axes,
            "series": series,
            "graphic": [{
                "type": "text",
                "right": 86,
                "top": 112,
                "style": {
                    "text": f"{TARGET_TEMP:.0f} °C 잔류량: {residue:.2f}%",
                    "fill": "#333",
                    "font": "bold 14px Noto Sans CJK KR",
                },
            }],
            "markLine": None,
        }

        # Mark the 700 °C point and residue value on the weight curve.
        series[0]["markLine"] = {
            "symbol": ["none", "none"],
            "lineStyle": {"color": "#d62728", "type": "dashed", "width": 1.5},
            "data": [{"xAxis": TARGET_TEMP, "label": {"formatter": "700 °C"}}],
        }
        series[0]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": "#d62728"},
            "label": {
                "show": True,
                "position": "top",
                "formatter": f"{residue:.2f}%",
            },
            "data": [{"coord": [TARGET_TEMP, residue]}],
        }

        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(sheet)).strip("_") or "plot"
        figures.append({
            "name": safe_name,
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
