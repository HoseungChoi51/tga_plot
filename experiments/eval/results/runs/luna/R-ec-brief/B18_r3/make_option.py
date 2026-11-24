import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
SHEET = "Annealed"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy(dtype=float)
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy(dtype=float)
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce").to_numpy(dtype=float)

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
order = np.argsort(temperature)
temperature, weight, dtg = temperature[order], weight[order], dtg[order]

# The largest mass-loss DTG peak above 150 °C is used for the extrapolated onset.
eligible = np.flatnonzero(temperature > 150)
peak_idx = int(eligible[np.argmin(dtg[eligible])])
peak_temp = float(temperature[peak_idx])

# Estimate the pre-event baseline from points immediately before the DTG event.
peak_magnitude = abs(float(dtg[peak_idx]))
threshold = max(peak_magnitude * 0.08, 1e-8)
start_idx = peak_idx
while start_idx > 0 and dtg[start_idx - 1] < -threshold:
    start_idx -= 1

baseline_end = max(0, start_idx)
baseline_start = max(0, baseline_end - 10)
if baseline_end - baseline_start < 3:
    baseline_start = max(0, peak_idx - 20)
    baseline_end = max(baseline_start + 1, peak_idx - 5)
baseline_weight = float(np.nanmean(weight[baseline_start:baseline_end]))

peak_weight = float(weight[peak_idx])
peak_slope = float(dtg[peak_idx])
if peak_slope < 0:
    onset_temp = peak_temp + (baseline_weight - peak_weight) / peak_slope
else:
    onset_temp = peak_temp
onset_weight = baseline_weight

# Residue at the measured point nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800.0)))
residue_temp = float(temperature[residue_idx])
residue_weight = float(weight[residue_idx])

x_min, x_max = float(np.min(temperature)), float(np.max(temperature))
y1_min, y1_max = float(np.min(weight)), float(np.max(weight))
y2 = (-dtg).tolist()
y2_min, y2_max = float(np.min(y2)), float(np.max(y2))
y1_pad = max(2.0, (y1_max - y1_min) * 0.06)
y2_pad = max(0.02, (y2_max - y2_min) * 0.08)

option = {
    "title": {
        "text": SHEET,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "legend": {"data": ["Weight", "DTG (-)"], "left": "center", "top": 38},
    "grid": {"left": 68, "right": 68, "top": 82, "bottom": 58},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 34,
        "min": x_min,
        "max": x_max,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": y1_min - y1_pad,
            "max": y1_max + y1_pad,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"color": "#1f4e9c"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
        },
        {
            "type": "value",
            "name": "DTG (-) (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": y2_min - y2_pad,
            "max": y2_max + y2_pad,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"color": "#c0392b"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "symbol": "circle",
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "data": [
                    {
                        "coord": [residue_temp, residue_weight],
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_weight:.1f}%",
                            "position": "top",
                            "color": "#1f4e9c"
                        }
                    },
                    {
                        "coord": [float(onset_temp), float(onset_weight)],
                        "label": {
                            "show": True,
                            "formatter": f"Onset {onset_temp:.1f} °C",
                            "position": "right",
                            "color": "#333333"
                        },
                        "itemStyle": {"color": "#333333"}
                    }
                ]
            },
            "markLine": {
                "symbol": ["none", "none"],
                "lineStyle": {"color": "#555555", "type": "dashed", "width": 1},
                "label": {"show": False},
                "data": [{"xAxis": float(onset_temp)}]
            }
        },
        {
            "name": "DTG (-)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 1.7},
            "data": [[float(x), float(y)] for x, y in zip(temperature, y2)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "data": [
                    {
                        "coord": [peak_temp, float(-dtg[peak_idx])],
                        "label": {
                            "show": True,
                            "formatter": f"{peak_temp:.0f} °C",
                            "position": "top",
                            "color": "#c0392b"
                        }
                    }
                ]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "annealed_onset",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
