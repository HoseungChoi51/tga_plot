import pandas as pd
import json

# Load the data
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"

# Try reading with different separators and header handling
try:
    # First try standard read_csv with whitespace separator
    df = pd.read_csv(file_path, sep=r'\s+', header=0)
except Exception:
    try:
        # Try tab separated
        df = pd.read_csv(file_path, sep='\t', header=0)
    except Exception:
        # Try comma separated just in case
        df = pd.read_csv(file_path, sep=',', header=0)

# Clean column names by stripping whitespace
df.columns = df.columns.str.strip()

# Identify columns based on content or position if names don't match exactly
cols = list(df.columns)

# Find time column (usually first numeric column starting with 0)
time_col = None
temp_col = None
weight_col = None

for col in cols:
    if 'time' in col.lower():
        time_col = col
    elif 'temperature' in col.lower() or 'temp' in col.lower():
        temp_col = col
    elif 'weight' in col.lower():
        weight_col = col

# Fallback to positional if keywords not found
if time_col is None:
    time_col = cols[0]
if temp_col is None:
    temp_col = cols[1]
if weight_col is None:
    weight_col = cols[2]

# Extract data arrays
times = df[time_col].dropna().tolist()
temps = df[temp_col].dropna().tolist()
weights = df[weight_col].dropna().tolist()

# Ensure lengths are consistent for pairing
min_len = min(len(times), len(temps), len(weights))
times = times[:min_len]
temps = temps[:min_len]
weights = weights[:min_len]

# Find weight at 140 min
weight_at_140 = None
for t, w in zip(times, weights):
    if abs(t - 140.0) < 1e-6:
        weight_at_140 = w
        break

# Prepare markPoint for 140 min
mark_point_data = []
if weight_at_140 is not None:
    mark_point_data.append({
        "coord": [140, weight_at_140],
        "value": f"{weight_at_140:.2f}%",
        "symbolSize": 10,
        "label": {
            "show": True,
            "position": "top",
            "formatter": "{c}"
        }
    })

option = {
    "title": {
        "text": "Isothermal TGA Data",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Temperature (°C)"],
        "top": 30
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%"
    },
    "xAxis": {
        "name": "Time (min)",
        "type": "value",
        "min": 0,
        "max": 140,
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "min": 70,
            "max": 105,
            "position": "left"
        },
        {
            "name": "Temperature (°C)",
            "type": "value",
            "min": 20,
            "max": 420,
            "position": "right",
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
            "data": [[t, w] for t, w in zip(times, weights)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#5470C6"
            },
            "markPoint": {
                "data": mark_point_data,
                "itemStyle": {
                    "color": "#EE6666"
                }
            }
        },
        {
            "name": "Temperature (°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[t, temp] for t, temp in zip(times, temps)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#91CC75"
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

print(json.dumps(result))
