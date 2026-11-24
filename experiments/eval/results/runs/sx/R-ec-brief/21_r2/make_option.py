import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"

# Read the Excel file, skipping the first 8 rows (header is at row 8, data starts at row 9)
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", skiprows=7)

# Extract columns: C -> Temperature, D -> Weight(%), E -> D.W(%/C)
temperature = df['Temperature'].values
weight = df['Weight(%)'].values
dtg = df['D.W(%/C)'].values

# Prepare data for ECharts
# For DTG, we multiply by -1 so peaks point up
dtg_negated = dtg * -1

# Find residue at ~800°C
idx_800 = np.argmin(np.abs(temperature - 800))
residue_temp = temperature[idx_800]
residue_weight = weight[idx_800]

# Find peak temperature of DTG above 150°C
mask_above_150 = temperature > 150
if np.any(mask_above_150):
    # We want the highest DTG peak (most negative original value, which becomes most positive after negation)
    dtg_for_peak = dtg.copy()
    dtg_for_peak[~mask_above_150] = np.inf  # exclude temps <= 150
    idx_peak = np.argmin(dtg_for_peak)  # minimum original DTG = maximum loss rate
    peak_temp = temperature[idx_peak]
else:
    peak_temp = None

# Build series data
series_weight = [[float(t), float(w)] for t, w in zip(temperature, weight)]
series_dtg = [[float(t), float(d)] for t, d in zip(temperature, dtg_negated)]

# Markers for residue and peak
mark_points = []
if residue_weight is not None:
    mark_points.append({
        "coord": [float(residue_temp), float(residue_weight)],
        "name": f"Residue {residue_weight:.1f}%",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_weight:.1f}%",
            "position": "top",
            "fontSize": 12,
            "color": "#1f4e9c"
        }
    })

if peak_temp is not None:
    # Find the DTG value at peak temp (negated)
    idx_pk = np.argmin(np.abs(temperature - peak_temp))
    dtg_val_at_peak = dtg_negated[idx_pk]
    mark_points_dtg = [{
        "coord": [float(peak_temp), float(dtg_val_at_peak)],
        "name": f"{peak_temp:.0f} °C",
        "symbolSize": 8,
        "itemStyle": {"color": "#c0392b"},
        "label": {
            "show": True,
            "formatter": f"{peak_temp:.0f} °C",
            "position": "top",
            "fontSize": 12,
            "color": "#c0392b"
        }
    }]
else:
    mark_points_dtg = []

option = {
    "title": {
        "text": "Sheet1",
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
        "orient": "vertical",
        "left": "left",
        "top": "middle",
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
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "axisTick": {
            "show": True
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10
        },
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisTick": {
                "show": True
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
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
            "nameLocation": "middle",
            "nameGap": 40,
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisTick": {
                "show": True
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
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
            "data": series_weight,
            "yAxisIndex": 0,
            "smooth": False,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "showSymbol": False,
            "markPoint": {
                "data": mark_points
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "data": series_dtg,
            "yAxisIndex": 1,
            "smooth": False,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "itemStyle": {
                "color": "#c0392b"
            },
            "showSymbol": False,
            "markPoint": {
                "data": mark_points_dtg
            }
        }
    ]
}

result = {
    "figures": [
        {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result, ensure_ascii=False))
