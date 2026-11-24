import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read the 'PET' sheet
    df = pd.read_excel(file_path, sheet_name='PET')
    
    # Extract data columns based on the preview
    # Temperature (°C) is column B, Weight (%) is column C, Deriv. Weight (%/°C) is column D
    temp = df['Temperature (°C)'].tolist()
    weight = df['Weight (%)'].round(2).tolist()  # Round to 2 decimal places for residual weight
    deriv_weight = df['Deriv. Weight (%/°C)'].tolist()
    
    # Create ECharts option
    option = {
        "title": {
            "text": "PET 열분해",
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": ["무게 (%)", "미분 무게 (%/°C)"],
            "bottom": 10,
            "left": "left"
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "15%",
            "containLabel": True,
            "show": True,
            "borderColor": "#ccc"
        },
        "xAxis": [
            {
                "type": "value",
                "name": "온도 (°C)",
                "min": 30,
                "max": 900,
                "splitLine": {"show": True}
            }
        ],
        "yAxis": [
            {
                "type": "value",
                "name": "무게 (%)",
                "min": 0,
                "max": 100,
                "splitLine": {"show": True},
                "position": "left"
            },
            {
                "type": "value",
                "name": "미분 무게 (%/°C)",
                "min": -2.0,
                "max": 0.01,
                "splitLine": {"show": False},
                "position": "right"
            }
        ],
        "series": [
            {
                "name": "무게 (%)",
                "type": "line",
                "data": list(zip(temp, weight)),
                "smooth": False,
                "symbol": "none",
                "yAxisIndex": 0
            },
            {
                "name": "미분 무게 (%/°C)",
                "type": "line",
                "data": list(zip(temp, deriv_weight)),
                "smooth": False,
                "symbol": "none",
                "yAxisIndex": 1
            }
        ]
    }
    
    figure = {
        "name": "pet_pyrolysis",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }
    
    result = {"figures": [figure]}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
