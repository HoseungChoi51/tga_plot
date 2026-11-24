import pandas as pd
import numpy as np
import json

def find_knee_temperatures(temp, weight):
    """
    Find two temperatures where the weight curve bends sharply (knees).
    We calculate the second derivative of weight with respect to temperature.
    The most negative peaks in the second derivative correspond to sharp drops/knees.
    To avoid noise, we smooth the data slightly or use a windowed approach.
    Here we use a simple numerical differentiation on smoothed data.
    """
    # Sort by temperature just in case
    df = pd.DataFrame({'T': temp, 'W': weight}).sort_values('T').reset_index(drop=True)
    
    # Calculate first derivative dW/dT
    # Using central difference approximation for interior points
    dW_dT = np.gradient(df['W'], df['T'])
    
    # Calculate second derivative d2W/dT2
    d2W_dT2 = np.gradient(dW_dT, df['T'])
    
    # We look for local minima in the second derivative (sharp downward curvature)
    # Since DTG is -dW/dT, large positive DTG means fast mass loss. 
    # A "knee" often corresponds to an inflection point where the slope changes rapidly.
    # Alternatively, knees can be identified as local maxima in the absolute value of the second derivative?
    # Actually, "무게가 확 꺾이는 데" usually implies the onset of rapid decomposition or distinct steps.
    # Let's identify the two most prominent peaks in the DTG curve (first derivative magnitude), 
    # as these represent the steepest slopes, which are visually the sharpest parts of the drop.
    # However, "knee" might refer to the start/end of plateaus. 
    # Given TGA context, users often want the peak temperatures of decomposition steps.
    # Let's stick to finding the two largest peaks in the DTG (absolute value) above 150C.
    
    dtg_abs = np.abs(-dW_dT) # Positive values for mass loss
    
    # Filter out low temperatures (< 150 C) and very small signals
    mask = (df['T'] > 150) & (dtg_abs > 0.01 * np.max(dtg_abs))
    if not np.any(mask):
        return []
        
    valid_T = df['T'][mask].values
    valid_DTG = dtg_abs[mask] # Removed .values because dtg_abs is already ndarray
    
    # Find local maxima in the filtered DTG
    # Simple peak detection: point higher than neighbors
    peaks = []
    for i in range(1, len(valid_DTG)-1):
        if valid_DTG[i] >= valid_DTG[i-1] and valid_DTG[i] >= valid_DTG[i+1]:
            # Avoid multiple peaks too close together (e.g., within 20 degrees)
            if not peaks or abs(valid_T[i] - peaks[-1][0]) > 20:
                peaks.append((valid_T[i], valid_DTG[i]))
                
    # Sort peaks by height (DTG magnitude) descending
    peaks.sort(key=lambda x: x[1], reverse=True)
    
    # Return top 2 temperatures
    return [float(p[0]) for p in peaks[:2]]

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
SHEET_NAME = "PVC"

# Read data
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# Identify columns based on standard names from preview
col_temp = "Temperature (°C)"
col_weight = "Weight (%)"
col_dtg = "Deriv. Weight (%/°C)"

temp = df[col_temp].values
weight = df[col_weight].values
dtg = df[col_dtg].values

# Find knee temperatures
knee_temps = find_knee_temperatures(temp, weight)

# Prepare ECharts Option
# Standard TGA Plot structure
title_text = SHEET_NAME

# Series 1: Weight (%)
series_weight = {
    "name": "Weight (%)",
    "type": "line",
    "yAxisIndex": 0,
    "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
    "showSymbol": False,
    "lineStyle": {"color": "#1f4e9c", "width": 2},
    "markPoint": {
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "position": "top",
            "formatter": "{b}",
            "fontSize": 12,
            "color": "#333"
        },
        "data": []
    }
}

# Add Knee Markers to Weight Series
for kt in knee_temps:
    # Find closest weight value at this temperature
    idx = np.argmin(np.abs(temp - kt))
    w_at_kt = weight[idx]
    series_weight["markPoint"]["data"].append({
        "coord": [float(kt), float(w_at_kt)],
        "value": f"{kt:.1f} °C"
    })

# Series 2: DTG (-DTG for upward peaks)
series_dtg = {
    "name": "DTG (-)",
    "type": "line",
    "yAxisIndex": 1,
    "data": [[float(t), float(-d)] for t, d in zip(temp, dtg)],
    "showSymbol": False,
    "lineStyle": {"color": "#c0392b", "width": 2}
}

option = {
    "title": {
        "text": title_text,
        "left": "center",
        "textStyle": {"fontSize": 16, "fontWeight": "bold"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["Weight (%)", "DTG (-)"],
        "orient": "vertical",
        "left": "left",
        "top": "middle"
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "offset": 0,
            "min": 0,
            "max": 100,
            "axisLine": {"lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"color": "#1f4e9c"}
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "offset": 0,
            "axisLine": {"lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"color": "#c0392b"}
        }
    ],
    "series": [series_weight, series_dtg]
}

figure = {
    "name": "plot1",
    "option": option,
    "width": 614,
    "height": 442,
    "dpi": 300,
    "formats": ["png"]
}

result = {"figures": [figure]}
print(json.dumps(result))
