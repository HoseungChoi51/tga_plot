import json
import re
import os

import numpy as np
import pandas as pd

DATA_FILE = os.environ.get(
    "DATA_FILE",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx",
)


def sanitize_name(name):
    name = str(name)
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")
    return name or "plot"


def find_column(df, keywords, exclude=None):
    exclude = exclude or []
    for col in df.columns:
        text = str(col).lower()
        if any(x in text for x in exclude):
            continue
        if any(k in text for k in keywords):
            return col
    return None


def build_tga_option(df, sheet_name):
    x_col = find_column(df, ["temperature", "temp", "°c", "℃"], exclude=["time"])
    y1_col = find_column(df, ["weight"], exclude=["deriv", "dtg"])
    y2_col = find_column(df, ["deriv", "dtg"], exclude=[])

    if x_col is None:
        for col in df.columns:
            text = str(col).lower()
            if "°c" in text or "℃" in text:
                x_col = col
                break

    if y1_col is None:
        for col in df.columns:
            text = str(col).lower()
            if "weight" in text and "%" in text and "deriv" not in text and "dtg" not in text:
                y1_col = col
                break

    if y2_col is None:
        for col in df.columns:
            text = str(col).lower()
            if "deriv" in text or "dtg" in text:
                y2_col = col
                break

    if x_col is None or y1_col is None or y2_col is None:
        cols = list(df.columns)
        if len(cols) >= 4:
            x_col = x_col or cols[1]
            y1_col = y1_col or cols[2]
            y2_col = y2_col or cols[3]
        elif len(cols) >= 3:
            x_col = x_col or cols[0]
            y1_col = y1_col or cols[1]
            y2_col = y2_col or cols[2]
        else:
            return None

    data = df[[x_col, y1_col, y2_col]].copy()
    data.columns = ["x", "y1", "y2"]
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna()

    if data.empty:
        return None

    data = data.sort_values("x")
    data["y2_plot"] = -data["y2"]

    weight_data = [[float(r.x), float(r.y1)] for r in data.itertuples(index=False)]
    dtg_data = [[float(r.x), float(r.y2_plot)] for r in data.itertuples(index=False)]

    series = [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": weight_data,
            "showSymbol": False,
            "smooth": False,
            "z": 2,
            "lineStyle": {"color": "#1f4e9c", "width": 1.5},
            "itemStyle": {"color": "#1f4e9c"},
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "smooth": False,
            "z": 2,
            "lineStyle": {"color": "#c0392b", "width": 1.5},
            "itemStyle": {"color": "#c0392b"},
        },
    ]

    residue_idx = (data["x"] - 800.0).abs().idxmin()
    residue_x = float(data.loc[residue_idx, "x"])
    residue_y = float(data.loc[residue_idx, "y1"])

    series.append(
        {
            "name": "Residue",
            "type": "scatter",
            "yAxisIndex": 0,
            "data": [
                {
                    "name": f"Residue {residue_y:.1f}%",
                    "value": [residue_x, residue_y],
                }
            ],
            "symbol": "circle",
            "symbolSize": 8,
            "z": 10,
            "itemStyle": {
                "color": "#1f4e9c",
                "borderColor": "#ffffff",
                "borderWidth": 1,
            },
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "color": "#1f4e9c",
                "fontSize": 12,
                "fontWeight": "bold",
            },
        }
    )

    peak_mask = data["x"] > 150.0
    if bool(peak_mask.any()):
        peak_idx = data.loc[peak_mask, "y2_plot"].idxmax()
        peak_x = float(data.loc[peak_idx, "x"])
        peak_y = float(data.loc[peak_idx, "y2_plot"])

        series.append(
            {
                "name": "DTG peak",
                "type": "scatter",
                "yAxisIndex": 1,
                "data": [
                    {
                        "name": f"{peak_x:.0f} °C",
                        "value": [peak_x, peak_y],
                    }
                ],
                "symbol": "circle",
                "symbolSize": 8,
                "z": 10,
                "itemStyle": {
                    "color": "#c0392b",
                    "borderColor": "#ffffff",
                    "borderWidth": 1,
                },
                "label": {
                    "show": True,
                    "formatter": "{b}",
                    "position": "top",
                    "color": "#c0392b",
                    "fontSize": 12,
                    "fontWeight": "bold",
                },
            }
        )

    option = {
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontSize": 16,
                "fontWeight": "bold",
                "color": "#333333",
            },
        },
        "legend": {
            "data": ["Weight (%)", "DTG (%/°C)"],
            "left": "left",
            "top": "middle",
            "orient": "vertical",
            "icon": "rect",
            "textStyle": {"fontSize": 12},
        },
        "grid": {
            "left": 80,
            "right": 80,
            "top": 70,
            "bottom": 60,
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 35,
            "inverse": True,
            "axisLabel": {"fontSize": 12},
            "axisLine": {"show": True},
            "splitLine": {"show": False},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 45,
                "position": "left",
                "axisLabel": {"fontSize": 12},
                "splitLine": {
                    "show": True,
                    "lineStyle": {"color": "#eeeeee"},
                },
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 50,
                "position": "right",
                "axisLabel": {"fontSize": 12},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    return option


def main():
    xls = pd.ExcelFile(DATA_FILE)
    sheet_names = xls.sheet_names

    if "Raw" in sheet_names:
        selected_sheets = ["Raw"]
    else:
        selected_sheets = sheet_names

    figures = []

    for sheet_name in selected_sheets:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
        option = build_tga_option(df, sheet_name)

        if option is not None:
            figures.append(
                {
                    "name": sanitize_name(sheet_name),
                    "option": option,
                    "width": 614,
                    "height": 442,
                    "dpi": 300,
                    "formats": ["png"],
                }
            )

    print(json.dumps({"figures": figures}, ensure_ascii=False))


if __name__ == "__main__":
    main()
