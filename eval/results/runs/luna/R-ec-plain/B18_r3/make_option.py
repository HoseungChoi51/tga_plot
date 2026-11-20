import json
import os
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the selected TGA sheet and identify temperature and weight columns.
df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
df.columns = [str(c).strip() for c in df.columns]

def find_col(pattern):
    for col in df.columns:
        if pattern in col.lower():
            return col
    raise ValueError(f"Could not find column matching {pattern!r}")

x_col = find_col("temperature")
y_col = find_col("weight")
x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
y = pd.to_numeric(df[y_col], errors="coerce").to_numpy()
valid = np.isfinite(x) & np.isfinite(y)
x, y = x[valid], y[valid]
order = np.argsort(x)
x, y = x[order], y[order]

# Estimate the principal mass-loss event from the steepest mass-loss slope.
# The onset is the intersection of the pre-event baseline and the tangent at
# the maximum mass-loss rate.
slope = np.gradient(y, x)
peak_idx = int(np.argmin(slope))
peak_temp = float(x[peak_idx])

# Fit the tangent locally around the steepest point for a less noisy estimate.
lo = max(0, peak_idx - 3)
hi = min(len(x), peak_idx + 4)
tangent_m, tangent_b = np.polyfit(x[lo:hi], y[lo:hi], 1)

# Fit a pre-event baseline to the high-retention region before the main event.
baseline_end = max(2, peak_idx - max(8, len(x) // 40))
baseline_start = max(0, baseline_end - max(20, len(x) // 12))
baseline_x = x[baseline_start:baseline_end]
baseline_y = y[baseline_start:baseline_end]
if len(baseline_x) < 2:
    baseline_start = 0
    baseline_end = max(2, peak_idx)
    baseline_x = x[baseline_start:baseline_end]
    baseline_y = y[baseline_start:baseline_end]

baseline_m, baseline_b = np.polyfit(baseline_x, baseline_y, 1)
denom = tangent_m - baseline_m
onset_temp = float((baseline_b - tangent_b) / denom) if abs(denom) > 1e-12 else peak_temp
if not np.isfinite(onset_temp):
    onset_temp = peak_temp

# Keep plotted series compact while preserving the measured curve shape.
weight_data = [[float(a), float(b)] for a, b in zip(x, y)]

option = {
    "backgroundColor": "#ffffff",
    "animation": False,
    "title": {
        "text": "Annealed TGA — 외삽 개시 온도",
        "left": "center",
        "top": 12,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 17, "fontWeight": "bold"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Weight (%)", "Onset"],
        "top": 42,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12},
    },
    "grid": {"left": 78, "right": 32, "top": 86, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": float(np.nanmin(x)),
        "max": float(np.nanmax(x)),
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 13},
        "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 13},
        "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": weight_data,
            "showSymbol": False,
            "lineStyle": {"color": "#2563a6", "width": 2},
            "emphasis": {"focus": "series"},
            "markLine": {
                "symbol": ["none", "none"],
                "silent": True,
                "lineStyle": {"color": "#d62728", "width": 1.6, "type": "dashed"},
                "label": {
                    "show": True,
                    "formatter": f"Onset {onset_temp:.1f} °C",
                    "position": "insideEndTop",
                    "color": "#b51f24",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12,
                },
                "data": [{"xAxis": onset_temp}],
            },
        },
        {
            "name": "Onset",
            "type": "scatter",
            "data": [[onset_temp, float(np.interp(onset_temp, x, y))]],
            "symbolSize": 10,
            "itemStyle": {"color": "#d62728", "borderColor": "#ffffff", "borderWidth": 1.5},
            "tooltip": {
                "valueFormatter": f"{onset_temp:.1f} °C",
            },
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "annealed_onset",
        "option": option,
        "width": 900,
        "height": 600,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
