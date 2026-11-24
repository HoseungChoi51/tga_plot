import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def get_tga_data(file_path):
    """Read TGA data from Excel file and return list of sheet data"""
    xl = pd.ExcelFile(file_path)
    sheets = []
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
        
        # Identify columns based on typical TGA naming
        temp_col = None
        weight_col = None
        dtg_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'temperature' in col_lower or 'temp' in col_lower:
                temp_col = col
            elif 'weight' in col_lower and '%' in col_lower:
                weight_col = col
            elif 'd.w' in col_lower or 'dtg' in col_lower or 'derivative' in col_lower:
                dtg_col = col
        
        if temp_col is None or weight_col is None or dtg_col is None:
            continue
        
        # Extract clean data
        temps = df[temp_col].dropna().values
        weights = df[weight_col].dropna().values
        dtgs = df[dtg_col].dropna().values
        
        # Align lengths
        min_len = min(len(temps), len(weights), len(dtgs))
        temps = temps[:min_len]
        weights = weights[:min_len]
        dtgs = dtgs[:min_len]
        
        # Find residue at 800°C (or nearest point)
        idx_800 = np.argmin(np.abs(temps - 800))
        residue_val = weights[idx_800]
        residue_temp = temps[idx_800]
        
        # Find peak DTG above 150°C
        mask_above_150 = temps > 150
        if np.any(mask_above_150):
            dtgs_filtered = dtgs[mask_above_150]
            temps_filtered = temps[mask_above_150]
            # Peak is the most negative value (largest mass loss rate)
            peak_idx_in_filtered = np.argmin(dtgs_filtered)
            peak_temp = temps_filtered[peak_idx_in_filtered]
            peak_dtg = dtgs_filtered[peak_idx_in_filtered]
        else:
            peak_temp = None
            peak_dtg = None
        
        sheets.append({
            'name': sheet_name,
            'temps': temps.tolist(),
            'weights': weights.tolist(),
            'dtgs': dtgs.tolist(),
            'residue_val': float(residue_val),
            'residue_temp': float(residue_temp),
            'peak_temp': float(peak_temp) if peak_temp is not None else None,
            'peak_dtg': float(peak_dtg) if peak_dtg is not None else None
        })
    
    return sheets


def create_tga_option(sheet_data):
    """Create ECharts option for a single TGA plot with shaded region 300-450°C"""
    
    temps = sheet_data['temps']
    weights = sheet_data['weights']
    dtgs = sheet_data['dtgs']
    residue_val = sheet_data['residue_val']
    residue_temp = sheet_data['residue_temp']
    peak_temp = sheet_data['peak_temp']
    peak_dtg = sheet_data['peak_dtg']
    
    # Prepare data series
    weight_data = [[t, w] for t, w in zip(temps, weights)]
    dtg_data = [[t, -d] for t, d in zip(temps, dtgs)]  # Multiply by -1 so peaks point up
    
    # Calculate axis ranges
    temp_min = min(temps)
    temp_max = max(temps)
    weight_min = min(weights)
    weight_max = max(weights)
    dtg_min = min(-d for d in dtgs)
    dtg_max = max(-d for d in dtgs)
    
    # Add some padding
    temp_range = temp_max - temp_min
    weight_range = weight_max - weight_min
    dtg_range = dtg_max - dtg_min
    
    y1_min = max(0, weight_min - weight_range * 0.1)
    y1_max = weight_max + weight_range * 0.1
    y2_min = dtg_min - dtg_range * 0.1
    y2_max = dtg_max + dtg_range * 0.1
    
    # Build markPoint data for residue and peak labels
    mark_points = []
    
    # Residue marker
    mark_points.append({
        "coord": [residue_temp, residue_val],
        "value": f"Residue {residue_val:.1f}%",
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_val:.1f}%",
            "position": "top",
            "fontSize": 11,
            "fontWeight": "bold",
            "color": "#1f4e9c"
        }
    })
    
    # Peak marker if exists
    if peak_temp is not None and peak_dtg is not None:
        peak_y = -peak_dtg  # Because we multiplied by -1
        mark_points.append({
            "coord": [peak_temp, peak_y],
            "value": f"{peak_temp:.0f} °C",
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_temp:.0f} °C",
                "position": "top",
                "fontSize": 11,
                "fontWeight": "bold",
                "color": "#c0392b"
            }
        })
    
    # Shaded region 300-450°C using markArea
    shade_start = 300
    shade_end = 450
    
    option = {
        "title": {
            "text": sheet_data['name'],
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontSize": 16,
                "fontFamily": "Noto Sans CJK KR",
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
            "data": ["Weight (%)", "DTG (%/°C)"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
            "textStyle": {
                "fontSize": 12,
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": 80,
            "right": 80,
            "top": 60,
            "bottom": 60,
            "containLabel": False
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": temp_min,
            "max": temp_max,
            "axisLabel": {
                "fontSize": 11,
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ddd"
                }
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": round(y1_min, 1),
                "max": round(y1_max, 1),
                "axisLabel": {
                    "fontSize": 11,
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "type": "dashed",
                        "color": "#ddd"
                    }
                }
            },
            {
                "type": "value",
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "min": round(y2_min, 2),
                "max": round(y2_max, 2),
                "axisLabel": {
                    "fontSize": 11,
                    "fontFamily": "Noto Sans CJK KR"
                },
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
                "data": weight_data,
                "smooth": False,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "showSymbol": False,
                "markArea": {
                    "silent": True,
                    "itemStyle": {
                        "color": "rgba(200, 200, 200, 0.3)"
                    },
                    "data": [
                        [
                            {"xAxis": shade_start},
                            {"xAxis": shade_end}
                        ]
                    ]
                },
                "markPoint": {
                    "data": mark_points
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dtg_data,
                "smooth": False,
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "itemStyle": {
                    "color": "#c0392b"
                },
                "showSymbol": False
            }
        ]
    }
    
    return option


def main():
    sheets = get_tga_data(DATA_FILE)
    
    figures = []
    for sheet in sheets:
        option = create_tga_option(sheet)
        fig = {
            "name": sheet['name'].replace(' ', '_').replace('-', '_'),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(fig)
    
    output = {"figures": figures}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
