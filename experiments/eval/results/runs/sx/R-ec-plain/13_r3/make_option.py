import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
    
    # Read the Excel file
    df = pd.read_excel(file_path, sheet_name="CNT-01")
    
    # Extract data for x-axis (Temperature) and y-axis (Weight mg)
    # Based on preview: Column B is Temperature, Column D is Weight (mg)
    temp = df["Temperature (°C)"].tolist()
    weight_mg = df["Weight (mg)"].tolist()
    
    # Create ECharts option
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": ["Weight"],
            "top": 10
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 25,
            "splitLine": {
                "show": False
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (mg)",
            "nameLocation": "middle",
            "nameGap": 40,
            "scale": True,
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "smooth": False,
                "symbol": "none",
                "data": list(zip(temp, weight_mg)),
                "lineStyle": {
                    "width": 2
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
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
