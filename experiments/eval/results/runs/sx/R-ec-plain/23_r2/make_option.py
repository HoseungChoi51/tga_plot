import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"

# Read the data file
# The error suggests encoding issues (UnicodeDecodeError). We will try to read with different encodings.
# Common encodings for Korean text files: 'utf-8', 'cp949' (Windows ANSI), 'latin1'.
df = None
encodings_to_try = ['utf-8', 'cp949', 'latin1']

for enc in encodings_to_try:
    try:
        # Use sep=None and engine='python' to handle whitespace delimiters automatically
        df = pd.read_csv(DATA_FILE, sep=None, engine='python', header=None, skiprows=10, encoding=enc)
        break
    except UnicodeDecodeError:
        continue
    except Exception as e:
        # If it's not a decode error but another parsing error, we might want to try other separators or just fail if all encodings fail on decode
        # However, usually if one encoding works, the rest of the structure should be fine if sep=None is used correctly.
        # Let's keep trying other encodings if this one fails due to decoding.
        continue

if df is None:
    raise ValueError("Could not read file with any tried encoding.")

# Ensure we have at least 4 columns
if df.shape[1] < 4:
    raise ValueError(f"Data does not have enough columns. Found {df.shape[1]}")

# Assign column names based on TGA guess: x=B (index 1), y1=C (index 2), y2=D (index 3)
x_col = df.iloc[:, 1].values  
y1_col = df.iloc[:, 2].values 
y2_col = df.iloc[:, 3].values 

# Convert to float, handling potential non-numeric entries by coercing errors to NaN
x_clean = pd.to_numeric(x_col, errors='coerce')
y1_clean = pd.to_numeric(y1_col, errors='coerce')
y2_clean = pd.to_numeric(y2_col, errors='coerce')

# Remove rows where any of the required values are NaN
mask = ~np.isnan(x_clean) & ~np.isnan(y1_clean) & ~np.isnan(y2_clean)
x_final = x_clean[mask]
y1_final = y1_clean[mask]
y2_final = y2_clean[mask]

if len(x_final) == 0:
    raise ValueError("No valid data points found after cleaning.")

# Prepare series data
series_data_1 = [[float(x), float(y)] for x, y in zip(x_final, y1_final)]
series_data_2 = [[float(x), float(y)] for x, y in zip(x_final, y2_final)]

# Calculate final residue for the label
final_residue = y1_final[-1]
residue_label = f"Residue: {final_residue:.2f}%"

# Construct ECharts option
option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA Analysis",
        "left": "center",
        "top": 10,
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
        "data": ["Mass (%)", "Derivative (%/min)", residue_label],
        "top": 40,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "15%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Mass (%)",
            "position": "left",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "min": 0,
            "max": 110,
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        {
            "type": "value",
            "name": "Derivative (%/min)",
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Mass (%)",
            "type": "line",
            "data": series_data_1,
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#5470c6"
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [float(x_final[-1]), float(y1_final[-1])],
                        "value": residue_label,
                        "itemStyle": {
                            "color": "#ee6666"
                        },
                        "label": {
                            "show": True,
                            "formatter": "{b}",
                            "position": "top",
                            "distance": 10,
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12,
                            "fontWeight": "bold"
                        }
                    }
                ]
            }
        },
        {
            "name": "Derivative (%/min)",
            "type": "line",
            "yAxisIndex": 1,
            "data": series_data_2,
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#91cc75"
            }
        }
    ]
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

print(json.dumps(output, ensure_ascii=False))
