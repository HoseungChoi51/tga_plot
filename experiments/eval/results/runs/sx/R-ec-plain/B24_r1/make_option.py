import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read the PE sheet
    df = pd.read_excel(file_path, sheet_name="PE")
    
    # Extract columns
    temp_c = df['Temperature (°C)'].values
    weight = df['Weight (%)'].values
    deriv_weight = df['Deriv. Weight (%/°C)'].values
    
    # Convert temperature to Kelvin
    temp_k = temp_c + 273.15
    
    # Prepare data for ECharts
    # TGA usually plots Weight % vs Temperature and DTG (Derivative) vs Temperature
    # We will create a dual-axis chart: Left axis for Weight %, Right axis for Deriv. Weight
    # X-axis is Temperature in Kelvin
    
    series_data_weight = []
    series_data_deriv = []
    
    for t, w, dw in zip(temp_k, weight, deriv_weight):
        if not (pd.isna(t) or pd.isna(w)):
            series_data_weight.append([round(float(t), 2), round(float(w), 4)])
        if not (pd.isna(t) or pd.isna(dw)):
            series_data_deriv.append([round(float(t), 2), round(float(dw), 6)])

    option = {
        "backgroundColor": "#ffffff",
        "title": {
            "text": "TGA Analysis of PE (Kelvin)",
            "subtext": "Weight Loss and Derivative Weight vs Temperature",
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 18,
                "fontWeight": "bold"
            },
            "subtextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            },
            "formatter": None # Using default formatter since we can't use JS functions easily in strict JSON without eval, but ECharts handles basic tooltips well.
        },
        "legend": {
            "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
            "top": 50,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (K)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": min(temp_k),
            "max": max(temp_k),
            "axisLabel": {
                "formatter": "{value} K",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLine": {
                    "lineStyle": {
                        "color": "#5470c6"
                    }
                },
                "axisLabel": {
                    "formatter": "{value} %",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "splitLine": {
                    "lineStyle": {
                        "type": "dashed"
                    }
                }
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "position": "right",
                "axisLine": {
                    "lineStyle": {
                        "color": "#ee6666"
                    }
                },
                "axisLabel": {
                    "formatter": "{value}",
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
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#5470c6"
                },
                "itemStyle": {
                    "color": "#5470c6"
                },
                "data": series_data_weight,
                "yAxisIndex": 0
            },
            {
                "name": "Deriv. Weight (%/°C)",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {
                    "width": 2,
                    "color": "#ee6666",
                    "type": "dashed"
                },
                "itemStyle": {
                    "color": "#ee6666"
                },
                "data": series_data_deriv,
                "yAxisIndex": 1
            }
        ]
    }

    figure = {
        "name": "pe_tga_kelvin",
        "option": option,
        "width": 800,
        "height": 500,
        "dpi": 150,
        "formats": ["png"]
    }

    output = {
        "figures": [figure]
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
