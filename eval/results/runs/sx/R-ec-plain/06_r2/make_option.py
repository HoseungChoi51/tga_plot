import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def load_tga_data(file_path):
    """Load TGA data from Excel file with multiple sheets."""
    xl = pd.ExcelFile(file_path)
    sheets = xl.sheet_names
    
    tga_data = {}
    for sheet in sheets:
        df = pd.read_excel(xl, sheet_name=sheet, header=0)
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Identify columns based on the preview
        temp_col = None
        weight_col = None
        dw_col = None
        
        for col in df.columns:
            if 'Temperature' in col or 'Temp' in col:
                temp_col = col
            elif 'Weight' in col and '%' in col:
                weight_col = col
            elif 'D.W' in col or 'DTG' in col or 'dW' in col.lower():
                dw_col = col
        
        if temp_col and weight_col and dw_col:
            tga_data[sheet] = {
                'temperature': df[temp_col].values,
                'weight': df[weight_col].values,
                'dtg': df[dw_col].values
            }
    
    return tga_data

def create_tga_chart(tga_data):
    """Create ECharts option for TGA curves (Weight % vs Temperature)."""
    
    series_list = []
    colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']
    
    for idx, (sheet_name, data) in enumerate(tga_data.items()):
        # Create [x, y] pairs for scatter/line chart
        points = []
        for temp, weight in zip(data['temperature'], data['weight']):
            if not np.isnan(temp) and not np.isnan(weight):
                points.append([float(temp), float(weight)])
        
        color_idx = idx % len(colors)
        series_list.append({
            "name": sheet_name,
            "type": "line",
            "showSymbol": False,
            "smooth": True,
            "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[color_idx]},
            "data": points
        })
    
    option = {
        "backgroundColor": "#ffffff",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "show": False  # Remove legend as requested
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "top": "10%",
            "bottom": "15%"
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "min": 0,
            "max": 105,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            }
        },
        "series": series_list
    }
    
    return option

def create_dtg_chart(tga_data):
    """Create ECharts option for DTG curves (dW/dT vs Temperature)."""
    
    series_list = []
    colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']
    
    for idx, (sheet_name, data) in enumerate(tga_data.items()):
        points = []
        for temp, dtg in zip(data['temperature'], data['dtg']):
            if not np.isnan(temp) and not np.isnan(dtg):
                points.append([float(temp), float(dtg)])
        
        color_idx = idx % len(colors)
        series_list.append({
            "name": sheet_name,
            "type": "line",
            "showSymbol": False,
            "smooth": True,
            "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[color_idx]},
            "data": points
        })
    
    option = {
        "backgroundColor": "#ffffff",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "show": False  # Remove legend as requested
        },
        "grid": {
            "left": "12%",
            "right": "10%",
            "top": "10%",
            "bottom": "15%"
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            }
        },
        "yAxis": {
            "type": "value",
            "name": "dW/dT (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 14
            }
        },
        "series": series_list
    }
    
    return option

def main():
    tga_data = load_tga_data(DATA_FILE)
    
    figures = []
    
    # TGA chart (Weight % vs Temperature)
    tga_option = create_tga_chart(tga_data)
    figures.append({
        "name": "tga_weight",
        "option": tga_option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })
    
    # DTG chart (dW/dT vs Temperature)
    dtg_option = create_dtg_chart(tga_data)
    figures.append({
        "name": "tga_dtg",
        "option": dtg_option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })
    
    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
