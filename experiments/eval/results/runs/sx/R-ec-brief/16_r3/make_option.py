import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet requested
sheet_name = "1006R1-V normal"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Extract columns based on standard TGA structure and preview info
# B: Temperature (x), C: Weight(%) (y1)
x_col = 'Temperature'
y1_col = 'Weight(%)'

# Prepare data for ECharts
# Filter out any NaN rows just in case
df_clean = df.dropna(subset=[x_col, y1_col])

temp_data = df_clean[x_col].tolist()
weight_data = df_clean[y1_col].tolist()

# Calculate Residue at 800°C (nearest point)
# The max temp is 900, so we can find nearest to 800
target_temp = 800.0
idx_nearest = np.argmin(np.abs(np.array(temp_data) - target_temp))
residue_val = weight_data[idx_nearest]
residue_label = f"Residue {residue_val:.1f}%"

# We need a marker for the residue point. 
# In ECharts line series, we can use markPoint or a separate scatter series.
# Using markPoint is cleaner for single points.
residue_x = temp_data[idx_nearest]
residue_y = residue_val

# Construct the ECharts option
option = {
    "title": {
        "text": sheet_name,
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "10%",
        "top": "15%",
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 25,
        "type": "value",
        "scale": True,
        "axisLine": {"lineStyle": {"color": "#333"}},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "type": "value",
        "scale": True,
        "axisLine": {"lineStyle": {"color": "#333"}},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": list(zip(temp_data, weight_data)),
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [residue_x, residue_y],
                        "value": residue_label,
                        "itemStyle": {
                            "color": "#1f4e9c"
                        },
                        "label": {
                            "show": True,
                            "formatter": "{b}",
                            "position": "top",
                            "distance": 10,
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 10,
                            "backgroundColor": "rgba(255,255,255,0.7)",
                            "padding": [2, 4],
                            "borderRadius": 2
                        },
                        "symbolSize": 8
                    }
                ]
            }
        }
    ],
    "legend": {
        "show": False # Only one series, legend might be redundant but user didn't explicitly ask to hide it, though usually simple plots omit if not needed. However, instructions say "legend at the center left" for standard TGA. Since this is a modified request ("no y2"), I will keep it minimal or hidden if it looks cluttered. Let's show it as per standard instruction unless it conflicts. Standard instruction says legend at center left.
    }
}

# Adjusting legend position to center-left as per general TGA instructions, even though there's only one series.
option["legend"] = {
    "orient": "vertical",
    "left": "left",
    "top": "middle",
    "data": ["Weight"],
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR"
    }
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
