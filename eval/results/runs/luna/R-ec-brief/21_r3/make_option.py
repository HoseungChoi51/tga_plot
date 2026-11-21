import json

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"


def number_or_none(value):
    try:
        result = float(value)
        return result if np.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def main():
    figures = []
    workbook = pd.ExcelFile(DATA_FILE)

    for sheet_name in workbook.sheet_names:
        raw = pd.read_excel(
            DATA_FILE, sheet_name=sheet_name, header=None, engine="openpyxl"
        )

        # Find the row containing the column headers, ignoring blank cells safely.
        header_row = None
        for idx in range(min(len(raw), 40)):
            cells = [
                str(value).strip().lower()
                for value in raw.iloc[idx].tolist()
                if pd.notna(value)
            ]
            if any("temperature" in cell for cell in cells) and any(
                "weight" in cell for cell in cells
            ):
                header_row = idx
                break

        if header_row is None:
            continue

        headers = raw.iloc[header_row].tolist()
        positions = {}
        for position, value in enumerate(headers):
            label = str(value).strip().lower() if pd.notna(value) else ""
            if "temperature" in label:
                positions["C"] = position
            if "weight" in label and "derivative" not in label and "d.w" not in label and "dw(" not in label:
                positions["D"] = position
            if "d.w" in label or "dw(" in label or "derivative" in label:
                positions["E"] = position

        if not all(column in positions for column in ("C", "D", "E")):
            continue

        body = raw.iloc[header_row + 1 :]
        x = pd.to_numeric(body.iloc[:, positions["C"]], errors="coerce")
        y1 = pd.to_numeric(body.iloc[:, positions["D"]], errors="coerce")
        y2_original = pd.to_numeric(body.iloc[:, positions["E"]], errors="coerce")
        valid = x.notna() & y1.notna() & y2_original.notna()

        x = x[valid].to_numpy(dtype=float)
        y1 = y1[valid].to_numpy(dtype=float)
        y2 = -y2_original[valid].to_numpy(dtype=float)
        if not len(x):
            continue

        weight_name = str(headers[positions["D"]]).strip()
        dtg_name = str(headers[positions["E"]]).strip()
        dtg_series_name = f"-{dtg_name}"

        option = {
            "animation": False,
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": [weight_name, dtg_series_name, "Residue", "DTG peak"],
                "left": 12,
                "top": "middle",
            },
            "grid": {"left": 78, "right": 78, "top": 58, "bottom": 65},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "splitLine": {"show": False},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": weight_name,
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {
                        "show": True,
                        "lineStyle": {"color": "#dddddd"},
                    },
                },
                {
                    "type": "value",
                    "name": dtg_series_name,
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": weight_name,
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "data": [
                        [number_or_none(a), number_or_none(b)]
                        for a, b in zip(x, y1)
                    ],
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                },
                {
                    "name": dtg_series_name,
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "data": [
                        [number_or_none(a), number_or_none(b)]
                        for a, b in zip(x, y2)
                    ],
                    "lineStyle": {"color": "#c0392b", "width": 2},
                },
            ],
        }

        residue_index = int(np.argmin(np.abs(x - 800.0)))
        option["series"][0]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": "#1f4e9c"},
            "label": {
                "show": True,
                "formatter": f"Residue {y1[residue_index]:.1f}%",
                "position": "right",
            },
            "data": [
                {
                    "coord": [
                        number_or_none(x[residue_index]),
                        number_or_none(y1[residue_index]),
                    ]
                }
            ],
        }

        eligible = np.flatnonzero(x > 150.0)
        if len(eligible):
            peak_index = int(eligible[np.argmax(y2[eligible])])
            option["series"][1]["markPoint"] = {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{x[peak_index]:.0f} °C",
                    "position": "right",
                },
                "data": [
                    {
                        "coord": [
                            number_or_none(x[peak_index]),
                            number_or_none(y2[peak_index]),
                        ]
                    }
                ],
            }

        figures.append(
            {
                "name": f"plot{len(figures) + 1}",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
