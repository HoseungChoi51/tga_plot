import pandas as pd
import numpy as np
import json
from scipy.signal import find_peaks

def main():
    file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
    
    # Read the PVC sheet
    df = pd.read_excel(file_path, sheet_name="PVC")
    
    # Extract relevant columns
    temp = df['Temperature (°C)'].values
    weight = df['Weight (%)'].values
    
    # Calculate derivative to find inflection points (steepest drops)
    # We use a simple numerical differentiation or just look at the provided derivative if available and reliable.
    # The prompt mentions "Deriv. Weight (%/°C)" in column D. Let's use that for accuracy as it's likely smoothed.
    deriv = df['Deriv. Weight (%/°C)'].values
    
    # Find peaks in the negative derivative (which correspond to steepest weight loss)
    # Since we want "steep drops", we look for minima in weight, which are maxima in |deriv| where deriv is negative.
    # Or simply find peaks in -deriv.
    negative_deriv = -deriv
    
    # Use find_peaks to identify significant drops
    # height: minimum prominence to be considered a peak
    # distance: minimum distance between peaks to avoid noise
    peaks, properties = find_peaks(negative_deriv, height=0.5, distance=20)
    
    mark_point_data = []
    if len(peaks) > 0:
        # Sort peaks by their value in negative_deriv (height of the peak) to get the most significant ones
        # properties might not have 'prominences' if not requested or depending on version, but 'peak_heights' is standard when height is used? 
        # Actually, find_peaks returns peak_heights in properties if height is specified? No, it returns 'peak_heights' only if you ask? 
        # Let's just sort by the value of negative_deriv at those indices.
        peak_values = negative_deriv[peaks]
        sorted_indices = np.argsort(peak_values)[::-1]
        top_peak_indices = peaks[sorted_indices[:2]] # Get top 2
        
        # Get temperatures for these peaks
        drop_temps = temp[top_peak_indices]
        
        for i, t in enumerate(drop_temps):
            # Find the corresponding weight value
            idx = np.where(temp == t)[0][0]
            w = weight[idx]
            mark_point_data.append({
                "coord": [float(t), float(w)],
                "name": f"Drop {i+1}",
                "value": f"{t:.1f}°C"
            })
            
    else:
        mark_point_data = []

    chart_option = {
        "title": {
            "text": "PVC TGA Curve with Major Decomposition Steps",
            "left": "center",
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        "tooltip": {
            "trigger": "axis",
            "formatter": "{a}<br/>Temp: {b} °C<br/>Weight: {c} %"
        },
        "legend": {
            "data": ["Weight"],
            "top": "10%"
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
            "min": 30,
            "max": 900,
            "axisLabel": {
                "formatter": "{value}"
            }
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 100
        },
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "smooth": False,
                "showSymbol": False,
                "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
                "markPoint": {
                    "symbolSize": 40,
                    "itemStyle": {
                        "color": "#FF4500"
                    },
                    "label": {
                        "show": True,
                        "formatter": "{@[0]}°C",
                        "fontSize": 12,
                        "fontWeight": "bold"
                    },
                    "data": mark_point_data
                }
            }
        ]
    }

    output = {
        "figures": [
            {
                "name": "pvc_tga_drops",
                "option": chart_option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
