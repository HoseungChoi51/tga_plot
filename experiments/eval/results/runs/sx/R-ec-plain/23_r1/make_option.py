import pandas as pd
import json

# Load the data file
file_path = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"

# The error indicates a UnicodeDecodeError with byte 0xff at position 0.
# This often means the file is UTF-16 LE or BE, or has a BOM (Byte Order Mark).
# Let's try reading with encoding='utf-16' first. If that fails, we might need to detect it.
# Common instrument exports are UTF-16.

try:
    df = pd.read_csv(file_path, sep=None, engine='python', header=None, skiprows=10, on_bad_lines='skip', encoding='utf-16')
except Exception:
    try:
        # Try utf-8-sig which handles BOM if present in utf-8 files
        df = pd.read_csv(file_path, sep=None, engine='python', header=None, skiprows=10, on_bad_lines='skip', encoding='utf-8-sig')
    except Exception:
        # Fallback to latin1 which accepts all bytes
        df = pd.read_csv(file_path, sep=None, engine='python', header=None, skiprows=10, on_bad_lines='skip', encoding='latin1')

# Ensure we have enough columns
if df.shape[1] < 4:
    # Pad missing columns if necessary, though unlikely given the preview said 4 columns
    pass

# Select the first 4 columns if there are more
df = df.iloc[:, :4]

# Assign column names based on context
df.columns = ['col_A', 'Temperature', 'Mass_Percent', 'Derivative']

# Convert to numeric, coercing errors to NaN
df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
df['Mass_Percent'] = pd.to_numeric(df['Mass_Percent'], errors='coerce')
df['Derivative'] = pd.to_numeric(df['Derivative'], errors='coerce')

# Drop rows where critical data is missing
df.dropna(subset=['Temperature', 'Mass_Percent', 'Derivative'], inplace=True)

# Extract data for plotting
x_data = df['Temperature'].tolist()
y_mass = df['Mass_Percent'].tolist()
y_deriv = df['Derivative'].tolist()

# Find the final residue (last mass percent value)
residue_value = y_mass[-1] if len(y_mass) > 0 else 0.0
residue_text = f"Residue: {residue_value:.2f}%"

# Construct ECharts option
option = {
    "title": {
        "text": "TGA Curve",
        "subtext": residue_text,
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Mass (%)", "Derivative (%/°C)"],
        "top": "bottom"
    },
    "grid": {
        "left": "3%",
        "right": "4%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "min": min(x_data) if x_data else 0,
        "max": max(x_data) if x_data else 1000
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Mass (%)",
            "position": "left",
            "min": 0,
            "max": 100
        },
        {
            "type": "value",
            "name": "Derivative (%/°C)",
            "position": "right"
        }
    ],
    "series": [
        {
            "name": "Mass (%)",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_mass)],
            "smooth": False,
            "showSymbol": False,
            "yAxisIndex": 0
        },
        {
            "name": "Derivative (%/°C)",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_deriv)],
            "smooth": False,
            "showSymbol": False,
            "yAxisIndex": 1,
            "lineStyle": {
                "width": 1,
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

print(json.dumps(output))
