import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_nearest_point(temp_arr, weight_arr, target_temp):
    idx = np.argmin(np.abs(temp_arr - target_temp))
    return temp_arr[idx], weight_arr[idx]

def create_tga_option(df, sheet_name):
    try:
        # Identify columns based on standard TGA structure from preview
        # Assuming column order: Time, Temperature, Weight(%), D.W(%/C)
        cols = df.columns.tolist()
        
        # Robustly find columns by name if possible, otherwise by index
        temp_col = None
        weight_col = None
        dtg_col = None
        
        for c in cols:
            c_lower = str(c).lower()
            if 'temp' in c_lower:
                temp_col = c
            elif 'weight' in c_lower or '%' in c_lower and 'dw' not in c_lower and 'd.w' not in c_lower:
                if weight_col is None: # First match for weight-like
                    weight_col = c
            elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower:
                dtg_col = c
                
        # Fallback to indices if names aren't clear
        if temp_col is None and len(cols) > 1: temp_col = cols[1]
        if weight_col is None and len(cols) > 2: weight_col = cols[2]
        if dtg_col is None and len(cols) > 3: dtg_col = cols[3]
        
        if temp_col is None or weight_col is None or dtg_col is None:
            return None

        temp = df[temp_col].values.astype(float)
        weight = df[weight_col].values.astype(float)
        dtg = df[dtg_col].values.astype(float)
        
        # Filter out NaNs just in case
        mask = ~np.isnan(temp) & ~np.isnan(weight) & ~np.isnan(dtg)
        temp = temp[mask]
        weight = weight[mask]
        dtg = dtg[mask]
        
        if len(temp) == 0:
            return None

        # Prepare data for ECharts series
        # Series 1: Weight (%) - Left Y Axis
        series_weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
        
        # Series 2: DTG (%/C) * -1 - Right Y Axis
        # Multiply by -1 so peaks point up as requested in standard plot description
        series_dtg_data = [[float(t), float(-d)] for t, d in zip(temp, dtg)]
        
        # Calculate Residue at nearest 800 C
        res_temp, res_weight = get_nearest_point(temp, weight, 800)
        
        option = {
            "title": {
                "text": sheet_name,
                "left": "center",
                "top": "2%",
                "textStyle": {
                    "fontSize": 14,
                    "fontWeight": "bold",
                    "color": "#333"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                }
            },
            "legend": {
                "data": ["Weight (%)", "DTG (-%/°C)"],
                "left": "left",
                "top": "middle",
                "orient": "vertical",
                "itemGap": 10
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
                "min": 0,
                "max": 900,
                "splitLine": {"show": False}
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "position": "left",
                    "min": 0,
                    "max": 110,
                    "splitLine": {"lineStyle": {"type": "dashed"}}
                },
                {
                    "type": "value",
                    "name": "DTG (-%/°C)",
                    "position": "right",
                    "splitLine": {"show": False}
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "yAxisIndex": 0,
                    "data": series_weight_data,
                    "smooth": False,
                    "symbol": "none",
                    "lineStyle": {
                        "color": "#1f4e9c",
                        "width": 2
                    },
                    "markPoint": {
                        "data": [
                            {
                                "coord": [res_temp, res_weight],
                                "value": f"Residue {res_weight:.1f}%",
                                "symbol": "circle",
                                "symbolSize": 6,
                                "itemStyle": {"color": "#1f4e9c"},
                                "label": {
                                    "show": True,
                                    "formatter": "{@[0]} °C\n{@[1]:.1f}%",
                                    "position": "right",
                                    "distance": 5,
                                    "fontSize": 10,
                                    "color": "#1f4e9c"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "DTG (-%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": series_dtg_data,
                    "smooth": False,
                    "symbol": "none",
                    "lineStyle": {
                        "color": "#c0392b",
                        "width": 2
                    }
                    # No markPoint for peak as per user request
                }
            ]
        }
        
        return option

    except Exception as e:
        return None

def main():
    figures = []
    
    try:
        xls = pd.ExcelFile(DATA_FILE)
        sheet_names = xls.sheet_names
        
        for sheet_name in sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # Drop rows where essential numeric columns are NaN
            # We assume the first few columns are relevant. 
            # A safer dropna might be needed depending on exact structure, but general dropna is often too aggressive if there are empty cells at end.
            # Let's rely on the helper function to handle valid data extraction.
            
            option = create_tga_option(df, sheet_name)
            
            if option is not None:
                fig_entry = {
                    "name": sheet_name.replace(" ", "_"),
                    "option": option,
                    "width": 614,
                    "height": 442,
                    "dpi": 300,
                    "formats": ["png"]
                }
                figures.append(fig_entry)
    except Exception as e:
        # If reading fails entirely, print empty figures list to avoid crash, though this indicates an issue
        pass
        
    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
