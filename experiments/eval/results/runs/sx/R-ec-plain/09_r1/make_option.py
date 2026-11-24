import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)

figures = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA naming conventions
    # Looking for Temperature (X), Weight(%) (Y1), D.W(%/C) (Y2)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'temperature' in col_str or 'temp' in col_str:
            temp_col = col
        elif 'weight' in col_str and '%' in col_str:
            weight_col = col
        elif 'd.w' in col_str or 'dtg' in col_str or 'derivative' in col_str:
            dtg_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    # Clean data: drop NaNs
    cols_to_use = [temp_col, weight_col] + ([dtg_col] if dtg_col else [])
    df_clean = df[cols_to_use].dropna()
    
    x_data = df_clean[temp_col].tolist()
    y_weight = df_clean[weight_col].tolist()
    
    series_list = []
    
    # TG Series
    series_list.append({
        "name": "TG",
        "type": "line",
        "data": [[x, y] for x, y in zip(x_data, y_weight)],
        "yAxisIndex": 0,
        "smooth": True,
        "showSymbol": False,
        "lineStyle": {"width": 2},
        "itemStyle": {"color": "#5470c6"}
    })
    
    # DTG Series if available
    if dtg_col:
        y_dtg = df_clean[dtg_col].tolist()
        series_list.append({
            "name": "DTG",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_dtg)],
            "yAxisIndex": 1,
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {"width": 2, "type": "dashed"},
            "itemStyle": {"color": "#ee6666"}
        })

    # Define axes options with tick direction outward and label size 9
    axis_common = {
        "axisTick": {"direction": "outward", "length": 5},
        "axisLabel": {"fontSize": 9},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
    }

    option = {
        "title": {
            "text": f"TGA - {sheet_name}",
            "left": "center",
            "top": "2%",
            "textStyle": {"fontSize": 14}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["TG"] + (["DTG"] if dtg_col else []),
            "top": "8%"
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            **axis_common,
            "min": min(x_data),
            "max": max(x_data)
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                **axis_common,
                "min": 0,
                "max": 110
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "position": "right",
                **axis_common,
                "offset": 0
            }
        ],
        "series": series_list
    }
    
    figures.append({
        "name": f"tga_{sheet_name.replace(' ', '_').replace('-', '_')}",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

output = {"figures": figures}
print(json.dumps(output))
