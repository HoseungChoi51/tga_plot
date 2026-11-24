import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

TEXT_COLOR = "#808080"
TEXT_SIZE = 13

def main():
    excel = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_name in excel.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        def find_column(candidates):
            for col in df.columns:
                normalized = col.lower().replace(" ", "")
                if any(candidate in normalized for candidate in candidates):
                    return col
            return None

        x_col = find_column(["temperature", "temp", "온도"])
        weight_col = find_column(["weight", "wt", "무게", "중량"])
        dtg_col = find_column(["d.w", "dtg", "derivative", "미분"])

        if x_col is None or weight_col is None or dtg_col is None:
            continue

        data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        x = data[x_col].tolist()
        weight = data[weight_col].tolist()
        dtg = data[dtg_col].tolist()

        residue_idx = min(range(len(x)), key=lambda i: abs(x[i] - 800))
        residue_temp = x[residue_idx]
        residue_value = weight[residue_idx]

        peak_candidates = [i for i, temp in enumerate(x) if temp > 150]
        if peak_candidates:
            peak_idx = max(peak_candidates, key=lambda i: -dtg[i])
            peak_temp = x[peak_idx]
            peak_height = -dtg[peak_idx]
            peak_text = f"{peak_temp:.0f} °C"
        else:
            peak_idx = None
            peak_temp = None
            peak_height = None
            peak_text = ""

        option = {
            "animation": False,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": TEXT_SIZE,
                "color": TEXT_COLOR
            },
            "title": {
                "text": sheet_name,
                "left": "center",
                "textStyle": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR}
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Weight (%)", "-DTG (%/°C)"],
                "left": "center",
                "bottom": 8,
                "textStyle": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR}
            },
            "grid": {"left": 75, "right": 75, "top": 65, "bottom": 75},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLabel": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                "nameTextStyle": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                "axisLine": {"lineStyle": {"color": TEXT_COLOR}},
                "axisTick": {"lineStyle": {"color": TEXT_COLOR}},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLabel": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                    "nameTextStyle": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                    "axisLine": {"show": True, "lineStyle": {"color": TEXT_COLOR}},
                    "axisTick": {"lineStyle": {"color": TEXT_COLOR}},
                    "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLabel": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                    "nameTextStyle": {"fontSize": TEXT_SIZE, "color": TEXT_COLOR},
                    "axisLine": {"show": True, "lineStyle": {"color": TEXT_COLOR}},
                    "axisTick": {"lineStyle": {"color": TEXT_COLOR}},
                    "splitLine": {"show": False}
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "showSymbol": False,
                    "data": [[a, b] for a, b in zip(x, weight)],
                    "lineStyle": {"width": 2, "color": "#1f4e9c"},
                    "itemStyle": {"color": "#1f4e9c"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_value:.1f}%",
                            "color": TEXT_COLOR,
                            "fontSize": TEXT_SIZE,
                            "position": "top"
                        },
                        "data": [{"coord": [residue_temp, residue_value]}]
                    }
                },
                {
                    "name": "-DTG (%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "data": [[a, -b] for a, b in zip(x, dtg)],
                    "lineStyle": {"width": 2, "color": "#c0392b"},
                    "itemStyle": {"color": "#c0392b"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": peak_text,
                            "color": TEXT_COLOR,
                            "fontSize": TEXT_SIZE,
                            "position": "top"
                        },
                        "data": [{"coord": [peak_temp, peak_height]}] if peak_idx is not None else []
                    }
                }
            ]
        }

        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in sheet_name)
        figures.append({
            "name": safe_name or "plot",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
