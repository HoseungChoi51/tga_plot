import json
import pandas as pd

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"
    
    # Read the data file. Assuming tab or whitespace separated based on .txt extension and typical TGA exports.
    # Trying sep='\t' first, then fallback to whitespace if needed, but usually these are consistent.
    try:
        df = pd.read_csv(file_path, sep='\t', header=0)
    except Exception:
        df = pd.read_csv(file_path, sep=r'\s+', header=0)

    # Clean column names just in case of extra spaces
    df.columns = [c.strip() for c in df.columns]
    
    time_col = "Time (min)"
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    
    # Extract data arrays
    times = df[time_col].tolist()
    temps = df[temp_col].tolist()
    weights = df[weight_col].tolist()
    
    # Find residue at 140 min
    # The user asks for weight at 140 min. 
    # We find the index closest to 140 minutes.
    target_time = 140.0
    idx_min = df[time_col].abs().sub(target_time).idxmin()
    
    residue_weight = df.loc[idx_min, weight_col]
    residue_time = df.loc[idx_min, time_col]
    
    # Prepare series data
    # Series 1: Weight (%) - Left Y Axis (yAxisIndex: 0)
    # Data format for line chart: [[x, y], ...]
    weight_data = [[t, w] for t, w in zip(times, weights)]
    
    # Series 2: Temperature (°C) - Right Y Axis (yAxisIndex: 1)
    temp_data = [[t, te] for t, te in zip(times, temps)]
    
    # Markers for residue
    # Add a scatter point or markPoint for the residue label
    # Using markPoint is cleaner for labels
    
    option = {
        "title": {
            "text": "Isothermal TGA",
            "left": "center",
            "top": "5%",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 16,
                "fontWeight": "bold"
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
            "data": ["Weight (%)", "Temperature (°C)"],
            "top": "10%",
            "right": "5%",
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
            "name": "Time (min)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "scale": False,
            "axisLine": {
                "lineStyle": {
                    "color": "#333"
                }
            },
            "axisTick": {
                "show": True,
                "alignWithLabel": True
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            }
        },
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#1f4e9c"
                    }
                },
                "axisTick": {
                    "show": True,
                    "lineStyle": {
                        "color": "#1f4e9c"
                    }
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "color": "#1f4e9c"
                },
                "splitLine": {
                    "show": False
                }
            },
            {
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 40,
                "type": "value",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#c0392b"
                    }
                },
                "axisTick": {
                    "show": True,
                    "lineStyle": {
                        "color": "#c0392b"
                    }
                },
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "color": "#c0392b"
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
                "symbol": "none",
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 2
                },
                "markPoint": {
                    "data": [
                        {
                            "coord": [residue_time, residue_weight],
                            "label": {
                                "show": True,
                                "formatter": f"Residue {residue_weight:.1f}%",
                                "position": "top",
                                "fontFamily": "Noto Sans CJK KR",
                                "fontSize": 12,
                                "color": "#1f4e9c",
                                "backgroundColor": "rgba(255,255,255,0.8)",
                                "borderColor": "#1f4e9c",
                                "borderWidth": 1,
                                "padding": [2, 4]
                            },
                            "symbol": "circle",
                            "symbolSize": 8,
                            "itemStyle": {
                                "color": "#1f4e9c"
                            }
                        }
                    ]
                }
            },
            {
                "name": "Temperature (°C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": temp_data,
                "smooth": False,
                "symbol": "none",
                "lineStyle": {
                    "color": "#c0392b",
                    "width": 2,
                    "type": "dashed"
                }
            }
        ]
    }

    result = {
        "figures": [
            {
                "name": "isothermal",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
