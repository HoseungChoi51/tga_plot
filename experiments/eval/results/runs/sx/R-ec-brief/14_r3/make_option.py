import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"

# Read the CSV file with encoding detection or fallback to cp949/euc-kr for Korean files
try:
    df = pd.read_csv(DATA_FILE, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(DATA_FILE, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_FILE, encoding='euc-kr')

# Extract columns based on TGA guess
x_col = "온도(°C)"
y1_col = "무게(%)"
y2_col = "미분무게(%/°C)"

temps = df[x_col].values
weights = df[y1_col].values
dtg = df[y2_col].values

# Invert DTG so peaks point up
dtg_inv = -dtg

# Find residue at nearest 800°C
idx_800 = np.argmin(np.abs(temps - 800))
residue_temp = temps[idx_800]
residue_weight = weights[idx_800]

# Find highest DTG peak above 150°C
mask = temps > 150
if mask.any():
    dtg_masked = dtg_inv[mask]
    temps_masked = temps[mask]
    max_idx = np.argmax(dtg_masked)
    peak_temp = temps_masked[max_idx]
    peak_val = dtg_masked[max_idx]
else:
    peak_temp = None
    peak_val = None

# Prepare data for ECharts
data_y1 = [[float(t), float(w)] for t, w in zip(temps, weights)]
data_y2 = [[float(t), float(d)] for t, d in zip(temps, dtg_inv)]

option = {
    "title": {
        "text": "korean_excel",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "DTG (%/°C)"],
        "left": "left",
        "top": "middle",
        "orient": "vertical",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": data_y1,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [float(residue_temp), float(residue_weight)],
                        "symbol": "circle",
                        "symbolSize": 8,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": f"Residue {residue_weight:.1f}%",
                            "fontSize": 12,
                            "color": "#1f4e9c",
                            "fontFamily": "Noto Sans CJK KR"
                        }
                    }
                ]
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_y2,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "markPoint": {
                "data": []
            }
        }
    ]
}

# Add peak marker to DTG series if found
if peak_temp is not None and peak_val is not None:
    option["series"][1]["markPoint"]["data"].append({
        "coord": [float(peak_temp), float(peak_val)],
        "symbol": "triangle",
        "symbolSize": 10,
        "itemStyle": {"color": "#c0392b"},
        "label": {
            "show": True,
            "position": "top",
            "formatter": f"{peak_temp:.0f} °C",
            "fontSize": 12,
            "color": "#c0392b",
            "fontFamily": "Noto Sans CJK KR"
        }
    })

output = {
    "figures": [
        {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png", "pdf"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
