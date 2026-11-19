import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def make_tga_option(df, sheet_name):
    # Identify columns based on the preview structure
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
    
    # Ensure data is sorted by temperature for proper line plotting
    df_sorted = df.sort_values(by=x_col)
    
    temps = df_sorted[x_col].tolist()
    weights = df_sorted[y1_col].tolist()
    dtg_raw = df_sorted[y2_col].tolist()
    
    # DTG multiplied by -1 so peaks point up
    dtg_negated = [-val for val in dtg_raw]
    
    # Calculate Residue at nearest 800°C
    # Find index of temperature closest to 800
    idx_800 = np.argmin(np.abs(np.array(temps) - 800))
    residue_val = weights[idx_800]
    temp_at_residue = temps[idx_800]
    
    # User requested to remove peak label, but we still need to know where it is if we were drawing markers.
    # Since "피크 표시 지워줘" means remove the peak label/marker, we just omit that specific markPoint or annotation.
    # However, standard TGA plots usually show the residue marker. The prompt says "two labels are always drawn... unless user says otherwise".
    # The user specifically said "피크 표시 지워줘" (Delete peak display). This implies keeping the residue display.
    
    residue_label_text = f"Residue {residue_val:.1f}%"
    
    # Determine axis ranges
    min_temp = min(temps)
    max_temp = max(temps)
    
    # Y1 range: Weight %
    min_w = min(weights)
    max_w = max(weights)
    # Add some padding
    w_padding = (max_w - min_w) * 0.1
    y1_min = max(0, min_w - w_padding) # Don't go below 0 typically for weight %
    y1_max = max_w + w_padding
    
    # Y2 range: DTG
    min_dtg = min(dtg_negated)
    max_dtg = max(dtg_negated)
    dtg_padding = (max_dtg - min_dtg) * 0.1
    y2_min = min_dtg - dtg_padding
    y2_max = max_dtg + dtg_padding
    
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
            "data": ["Weight (%)", "DTG (%/°C)"],
            "top": "middle",
            "left": "5%",
            "orient": "vertical",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": [
            {
                "name": "Temperature (°C)",
                "type": "value",
                "min": min_temp,
                "max": max_temp,
                "axisLabel": {
                    "formatter": "{value}",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "yAxis": [
            {
                "name": "Weight (%)",
                "type": "value",
                "position": "left",
                "min": y1_min,
                "max": y1_max,
                "axisLabel": {
                    "formatter": "{value}",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#eee"
                    }
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "value",
                "position": "right",
                "min": y2_min,
                "max": y2_max,
                "axisLabel": {
                    "formatter": "{value}",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "nameTextStyle": {
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
                "data": list(zip(temps, weights)),
                "yAxisIndex": 0,
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "lineStyle": {
                    "width": 2
                },
                "symbol": "none",
                "markPoint": {
                    "data": [
                        {
                            "coord": [temp_at_residue, residue_val],
                            "symbolSize": 10,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            },
                            "label": {
                                "show": True,
                                "formatter": residue_label_text,
                                "position": "right",
                                "offset": [5, 0],
                                "fontFamily": "Noto Sans CJK KR",
                                "fontSize": 10,
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                }
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "data": list(zip(temps, dtg_negated)),
                "yAxisIndex": 1,
                "itemStyle": {
                    "color": "#c0392b"
                },
                "lineStyle": {
                    "width": 2
                },
                "symbol": "none"
                # No markPoint for peak as per user request
            }
        ]
    }
    
    return option

def main():
    xls = pd.ExcelFile(DATA_FILE)
    figures = []
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Basic cleaning if needed, though headers seem clean
        # Map column names to expected keys if they vary slightly, but here they match preview
        
        option = make_tga_option(df, sheet_name)
        
        figure = {
            "name": f"plot_{sheet_name.replace(' ', '_')}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
        figures.append(figure)
        
    output = {"figures": figures}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
