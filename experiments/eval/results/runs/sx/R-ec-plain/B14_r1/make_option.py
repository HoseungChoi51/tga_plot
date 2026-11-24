import pandas as pd
import json

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read the PVC sheet
    df = pd.read_excel(file_path, sheet_name="PVC")
    
    # Extract data columns based on preview: B=Temperature, C=Weight, D=Deriv Weight
    temp = df['Temperature (°C)'].tolist()
    weight = df['Weight (%)'].tolist()
    deriv_weight = df['Deriv. Weight (%/°C)'].tolist()
    
    # Prepare series data for TGA (Weight %) and DTG (Deriv. Weight)
    tga_data = [[t, w] for t, w in zip(temp, weight)]
    dtg_data = [[t, d] for t, d in zip(temp, deriv_weight)]
    
    # Define ECharts option
    # Width 10 inches at 96 dpi -> 960 px. Height chosen proportionally, e.g., 7 inches -> 672 px.
    width_px = int(10 * 96)
    height_px = int(7 * 96)
    
    option = {
        "backgroundColor": "#ffffff",
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "textStyle": {"fontSize": 14}
        },
        "legend": {
            "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
            "top": "5%",
            "textStyle": {"fontSize": 16}
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "bottom": "10%",
            "containLabel": True
        },
        "xAxis": [
            {
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 35,
                "nameTextStyle": {"fontSize": 16},
                "type": "value",
                "min": 0,
                "max": 950,
                "axisLabel": {"fontSize": 16},
                "splitLine": {"show": False}
            }
        ],
        "yAxis": [
            {
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 50,
                "nameTextStyle": {"fontSize": 16},
                "type": "value",
                "min": 0,
                "max": 105,
                "axisLabel": {"fontSize": 16},
                "position": "left"
            },
            {
                "name": "Deriv. Weight (%/°C)",
                "nameLocation": "middle",
                "nameGap": 50,
                "nameTextStyle": {"fontSize": 16},
                "type": "value",
                "min": -1.2,
                "max": 0.1,
                "axisLabel": {"fontSize": 16},
                "position": "right",
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {"width": 3, "color": "#2E86AB"},
                "itemStyle": {"color": "#2E86AB"},
                "data": tga_data,
                "yAxisIndex": 0
            },
            {
                "name": "Deriv. Weight (%/°C)",
                "type": "line",
                "smooth": True,
                "symbol": "none",
                "lineStyle": {"width": 3, "color": "#A23B72"},
                "itemStyle": {"color": "#A23B72"},
                "data": dtg_data,
                "yAxisIndex": 1
            }
        ]
    }
    
    result = {
        "figures": [
            {
                "name": "pvc_tga_dtg",
                "option": option,
                "width": width_px,
                "height": height_px,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
