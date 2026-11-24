import pandas as pd
import json

def load_data(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        # Assuming tab or space separated for .txt, but pandas default might handle it or we need sep.
        # The preview shows columns like "Time (min)", so likely tab or comma delimited inside txt too? 
        # Standard practice for these TGA exports is often tab-delimited text.
        try:
            df = pd.read_csv(file_path, sep='\t')
        except:
            df = pd.read_csv(file_path, sep=',')
    
    # Clean column names just in case
    df.columns = [c.strip() for c in df.columns]
    return df

file_a = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv"
file_b = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt"

df_a = load_data(file_a)
df_b = load_data(file_b)

# Identify columns based on the preview info
# X: Temperature (°C), Y1: Weight (%), Y2: Deriv. Weight (%/°C)
x_col = 'Temperature (°C)'
y1_col = 'Weight (%)'
y2_col = 'Deriv. Weight (%/°C)'

# Prepare data for ECharts
# Series 1: Lot A Weight
data_a_weight = []
for _, row in df_a.iterrows():
    temp = float(row[x_col])
    weight = float(row[y1_col])
    data_a_weight.append([temp, weight])

# Series 2: Lot B Weight
data_b_weight = []
for _, row in df_b.iterrows():
    temp = float(row[x_col])
    weight = float(row[y1_col])
    data_b_weight.append([temp, weight])

# Series 3: Lot A DTG (Derivative)
data_a_dtg = []
for _, row in df_a.iterrows():
    temp = float(row[x_col])
    dtg = float(row[y2_col])
    data_a_dtg.append([temp, dtg])

# Series 4: Lot B DTG (Derivative)
data_b_dtg = []
for _, row in df_b.iterrows():
    temp = float(row[x_col])
    dtg = float(row[y2_col])
    data_b_dtg.append([temp, dtg])

option = {
    "title": {
        "text": "TGA Comparison: Lot A vs Lot B",
        "left": "center",
        "top": "5%",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 18
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        },
        "formatter": "{a} <br/>{b}: {c}"
    },
    "legend": {
        "data": ["Lot A Weight", "Lot B Weight", "Lot A DTG", "Lot B DTG"],
        "top": "10%"
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
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Lot A Weight",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 0,
            "data": data_a_weight,
            "itemStyle": {
                "color": "#5470C6"
            }
        },
        {
            "name": "Lot B Weight",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 0,
            "data": data_b_weight,
            "itemStyle": {
                "color": "#91CC75"
            }
        },
        {
            "name": "Lot A DTG",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 1,
            "data": data_a_dtg,
            "itemStyle": {
                "color": "#FAC858"
            },
            "lineStyle": {
                "type": "dashed"
            }
        },
        {
            "name": "Lot B DTG",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 1,
            "data": data_b_dtg,
            "itemStyle": {
                "color": "#EE6666"
            },
            "lineStyle": {
                "type": "dashed"
            }
        }
    ]
}

output = {
    "figures": [
        {
            "name": "tga_comparison",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
