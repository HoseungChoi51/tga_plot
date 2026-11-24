import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def read_sheet(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    # Identify columns based on the preview structure
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
    
    # Clean data: drop NaNs
    df = df.dropna(subset=[x_col, y1_col, y2_col])
    
    x = df[x_col].tolist()
    y1 = df[y1_col].tolist()
    y2_raw = df[y2_col].tolist()
    # Multiply DTG by -1 so peaks point up
    y2 = [-val for val in y2_raw]
    
    return x, y1, y2

def find_residue(x, y1, target_temp=800):
    """Find weight at temperature nearest to 800 C"""
    if not x or not y1:
        return None, None, None
    idx = np.argmin(np.abs(np.array(x) - target_temp))
    temp_at_idx = x[idx]
    weight_at_idx = y1[idx]
    return temp_at_idx, weight_at_idx, idx

def find_peak(x, y2, min_temp=150):
    """Find temperature of highest DTG peak above 150 C"""
    if not x or not y2:
        return None, None, None
    
    # Filter points where temperature > 150
    valid_indices = [i for i, t in enumerate(x) if t >= min_temp]
    if not valid_indices:
        return None, None, None
        
    valid_y2 = [y2[i] for i in valid_indices]
    max_val = max(valid_y2)
    local_idx = valid_y2.index(max_val)
    global_idx = valid_indices[local_idx]
    
    peak_temp = x[global_idx]
    peak_val = y2[global_idx] # This is already multiplied by -1 (positive value for loss)
    
    return peak_temp, peak_val, global_idx

def create_option(sheet_name, x, y1, y2):
    residue_temp, residue_weight, res_idx = find_residue(x, y1, 800)
    peak_temp, peak_val, pk_idx = find_peak(x, y2, 150)
    
    # Prepare markPoint data
    mark_points = []
    if residue_temp is not None and residue_weight is not None:
        mark_points.append({
            "coord": [residue_temp, residue_weight],
            "value": f"Residue {residue_weight:.1f}%",
            "symbolSize": 8,
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}",
                "fontSize": 10,
                "color": "#333"
            }
        })
        
    if peak_temp is not None and peak_val is not None:
        # Note: The marker should be on the curve. 
        # Since y2 axis shows -DTG, the peak value plotted is positive.
        # We need to map this back to the y2 axis value which is also positive now.
        mark_points.append({
            "coord": [peak_temp, peak_val],
            "value": f"{peak_temp:.0f} °C",
            "symbolSize": 8,
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}",
                "fontSize": 10,
                "color": "#333"
            },
            "seriesIndex": 1 # Attach to second series (DTG)
        })

    option = {
        "title": {
            "text": sheet_name,
            "left": "center",
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
        "legend": {
            "data": ["Weight (%)", "-DTG (%/°C)"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "15%",
            "right": "15%",
            "bottom": "15%",
            "containLabel": False
        },
        "xAxis": {
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 25,
            "type": "value",
            "min": 0,
            "max": 900,
            "splitLine": {"show": False},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "min": 0,
                "max": 110,
                "splitLine": {"show": True, "lineStyle": {"color": "#ccc"}},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                }
            },
            {
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "splitLine": {"show": False},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "color": "#27ae60" # Green color for label text
                },
                "axisLine": {
                    "lineStyle": {
                        "color": "#27ae60"
                    }
                }
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": [[x[i], y1[i]] for i in range(len(x))],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [mp for mp in mark_points if mp.get("seriesIndex") != 1]
                }
            },
            {
                "name": "-DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": [[x[i], y2[i]] for i in range(len(x))],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {
                    "color": "#27ae60", # Green color for line
                    "width": 2
                },
                "markPoint": {
                    "data": [mp for mp in mark_points if mp.get("seriesIndex") == 1]
                }
            }
        ]
    }
    return option

def main():
    file_path = DATA_FILE
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    
    figures = []
    for sheet in sheets:
        x, y1, y2 = read_sheet(file_path, sheet)
        if len(x) == 0:
            continue
        option = create_option(sheet, x, y1, y2)
        fig_entry = {
            "name": f"plot_{sheet.replace(' ', '_').replace('-', '_')}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(fig_entry)
        
    output = {"figures": figures}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
