import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"

def main():
    # Read the CSV file with explicit encoding handling for Korean text
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(DATA_FILE, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(DATA_FILE, encoding='latin1')
    
    # Identify columns based on the preview
    x_col = "온도(°C)"
    y1_col = "무게(%)"
    y2_col = "미분무게(%/°C)"
    
    # Extract data
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Prepare data for ECharts
    # We need to pair temperature with weight and temperature with DTG (negated)
    # ECharts line series expects [[x, y], [x, y], ...] format
    
    weight_data = []
    dtg_data = []
    
    for t, w, d in zip(temp, weight, dtg):
        if not (np.isnan(t) or np.isnan(w)):
            weight_data.append([float(t), float(w)])
        if not (np.isnan(t) or np.isnan(d)):
            # Negate DTG so peaks point up
            dtg_data.append([float(t), float(-d)])
            
    # Calculate Residue at 800°C
    residue_val = None
    residue_temp = None
    if len(weight_data) > 0:
        # Find index closest to 800°C
        temps_only = [item[0] for item in weight_data]
        idx_800 = min(range(len(temps_only)), key=lambda i: abs(temps_only[i] - 800))
        residue_temp = temps_only[idx_800]
        residue_val = weight_data[idx_800][1]
        
    # Calculate Peak Temperature (highest DTG peak above 150°C)
    peak_temp = None
    peak_dtg_val = None
    if len(dtg_data) > 0:
        # Filter data above 150°C
        filtered_dtg = [(t, d) for t, d in dtg_data if t >= 150]
        if filtered_dtg:
            # Find max DTG value (which is positive now because we negated it)
            max_idx = max(range(len(filtered_dtg)), key=lambda i: filtered_dtg[i][1])
            peak_temp = filtered_dtg[max_idx][0]
            peak_dtg_val = filtered_dtg[max_idx][1]
            
    # Build Option
    option = {
        "title": {
            "text": "korean_excel",
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": "{a}: {c}<br/>온도: {b} °C"
        },
        "legend": {
            "data": ["무게(%)", "-미분무게(%/°C)"],
            "orient": "vertical",
            "left": "left",
            "top": "middle",
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
        "xAxis": {
            "name": "온도(°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": 30,
            "max": 900,
            "splitLine": {
                "show": False
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "yAxis": [
            {
                "name": "무게(%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "left",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed"
                    }
                }
            },
            {
                "name": "-미분무게(%/°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": "무게(%)",
                "type": "line",
                "data": weight_data,
                "yAxisIndex": 0,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [residue_temp, residue_val],
                            "symbolSize": 8,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            },
                            "label": {
                                "show": True,
                                "formatter": f"Residue {residue_val:.1f}%",
                                "position": "right",
                                "distance": 10,
                                "fontFamily": "Noto Sans CJK KR",
                                "fontSize": 12,
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                }
            },
            {
                "name": "-미분무게(%/°C)",
                "type": "line",
                "data": dtg_data,
                "yAxisIndex": 1,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [peak_temp, peak_dtg_val],
                            "symbolSize": 8,
                            "itemStyle": {
                                "color": "#c0392b"
                            },
                            "label": {
                                "show": True,
                                "formatter": f"{int(peak_temp)} °C",
                                "position": "top",
                                "distance": 10,
                                "fontFamily": "Noto Sans CJK KR",
                                "fontSize": 12,
                                "color": "#c0392b"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    result = {
        "figures": [
            {
                "name": "plot1",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png", "pdf"]
            }
        ]
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
