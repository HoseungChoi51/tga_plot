import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheets = xls.sheet_names

data_dict = {}
for sheet in sheets:
    df = pd.read_excel(xls, sheet_name=sheet, header=0)
    data_dict[sheet] = df

# Prepare series data for TGA (Weight%) and DTG (D.W %/C)
# We'll create one chart with two y-axes: left for Weight(%), right for D.W(%/C)
series_tga = []
series_dtg = []

colors = ['#5470c6', '#91cc75', '#fac858']  # default echarts colors or custom gray-ish? User asked for text gray. Let's use distinct colors for lines.
# Actually user only specified text color and size. Lines can be default or we pick readable ones.
# Let's stick to standard distinguishable colors but ensure text is gray.

line_colors = ['#2F4F4F', '#4682B4', '#CD853F'] # Dark Slate Gray, Steel Blue, Peru - reasonable for lab

for i, sheet in enumerate(sheets):
    df = data_dict[sheet]
    temp = df['Temperature'].tolist()
    weight = df['Weight(%)'].tolist()
    dtg = df['D.W(%/C)'].tolist()
    
    # Clean NaNs if any just in case
    valid_indices = [j for j in range(len(temp)) if pd.notna(temp[j]) and pd.notna(weight[j])]
    clean_temp = [temp[j] for j in valid_indices]
    clean_weight = [weight[j] for j in valid_indices]
    clean_dtg = [dtg[j] for j in valid_indices]
    
    label = sheet.replace('1006R1-V ', '')
    
    series_tga.append({
        "name": f"{label} TG",
        "type": "line",
        "xAxisIndex": 0,
        "yAxisIndex": 0,
        "data": [[t, w] for t, w in zip(clean_temp, clean_weight)],
        "smooth": False,
        "symbol": "none",
        "lineStyle": {"width": 1.5, "color": line_colors[i]}
    })
    
    series_dtg.append({
        "name": f"{label} DTG",
        "type": "line",
        "xAxisIndex": 0,
        "yAxisIndex": 1,
        "data": [[t, d] for t, d in zip(clean_temp, clean_dtg)],
        "smooth": False,
        "symbol": "none",
        "lineStyle": {"width": 1.5, "color": line_colors[i], "type": "dashed"}
    })

all_series = series_tga + series_dtg

option = {
    "backgroundColor": "#FFFFFF",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR",
        "fontSize": 13,
        "color": "#808080"  # Gray color for all text
    },
    "title": {
        "text": "TGA / DTG Analysis",
        "left": "center",
        "textStyle": {
            "fontSize": 16,
            "color": "#808080"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": [s["name"] for s in all_series],
        "top": 30,
        "textStyle": {
            "color": "#808080",
            "fontSize": 13
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
        "axisLine": {
            "lineStyle": {
                "color": "#808080"
            }
        },
        "axisTick": {
            "lineStyle": {
                "color": "#808080"
            }
        },
        "axisLabel": {
            "color": "#808080",
            "fontSize": 13
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
            "axisLine": {
                "lineStyle": {
                    "color": "#808080"
                }
            },
            "axisTick": {
                "lineStyle": {
                    "color": "#808080"
                }
            },
            "axisLabel": {
                "color": "#808080",
                "fontSize": 13
            },
            "splitLine": {
                "lineStyle": {
                    "color": "#E0E0E0"
                }
            }
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "axisLine": {
                "lineStyle": {
                    "color": "#808080"
                }
            },
            "axisTick": {
                "lineStyle": {
                    "color": "#808080"
                }
            },
            "axisLabel": {
                "color": "#808080",
                "fontSize": 13
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": all_series
}

output = {
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

print(json.dumps(output))
