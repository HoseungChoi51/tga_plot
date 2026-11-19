import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

# Read the CSV file
df = pd.read_csv(DATA_FILE)

# Filter data for x range 100 to 900 °C
mask = (df['Temperature (°C)'] >= 100) & (df['Temperature (°C)'] <= 900)
filtered_df = df[mask].copy()

# Find residue at 900 °C (last point in filtered data, closest to 900)
residue_point = filtered_df.iloc[-1]
residue_temp = residue_point['Temperature (°C)']
residue_weight = residue_point['Weight (%)']

# Prepare data for ECharts
x_data = filtered_df['Temperature (°C)'].tolist()
y_data = filtered_df['Weight (%)'].tolist()

# Build the ECharts option
option = {
    "title": {
        "text": "TGA Weight Curve",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}<br/>Temperature: {b} °C<br/>Weight: {c} %"
    },
    "grid": {
        "left": 70,
        "right": 50,
        "top": 60,
        "bottom": 50
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "min": 100,
        "max": 900,
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_data)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#1f77b4"
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [residue_temp, residue_weight],
                        "symbolSize": 8,
                        "itemStyle": {"color": "#d62728"},
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": f"Residue @ {residue_temp:.0f}°C: {residue_weight:.2f}%",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12,
                            "color": "#d62728"
                        }
                    }
                ]
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
